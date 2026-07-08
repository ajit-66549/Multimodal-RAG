from uuid import uuid4
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from typing import Annotated
from fastapi import Query
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db
from app.models import Documents, DocumentChunk, DocumentAsset
from app.ingestion import process_pdf_into_chunks
from app.embedding_service import create_embeddings
from app.vector_store import add_chunk_embedding, query_chunks, add_asset_embedding, delete_document_embeddings
from app.llm_services import generate_answer
from app.csv_ingestion import process_csv_into_chunks
from app.image_extraction import extract_pdf_page_images
from app.ocr_service import extract_text_from_image

from app.s3_service import upload_file_to_s3, get_s3_object_byte, generate_presigned_URL

UPLOAD_DIR = Path("../storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".png", ".jpg", ".jpeg"}
    
app = FastAPI(title="HPC Multimodal RAG Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
# health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "hpc-rag-analyzer"
    }

# upload documents endpoint
@app.post("/documents/upload")
async def upload_documents(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    original_name = file.filename
    
    if not original_name:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    file_ext = Path(original_name).suffix.lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    document_id = str(uuid4())
    saved_name = f"{document_id}{file_ext}"
    saved_path = UPLOAD_DIR / saved_name
    
    content = await file.read()
    
    with open(saved_path, "wb") as f:
        f.write(content)
        
    document = Documents(
        id=document_id,
        filename=original_name,
        file_type=file_ext,
        storage_path=str(saved_path),
        status="uploaded"
    )
    
    db.add(document)
    await db.commit()
    db.refresh(document)
        
    return {
        "document_id": document_id,
        "filename": original_name,
        "saved_as": saved_name,
        "file_type": file_ext,
        "status": "uploaded"
    }
    
@app.get("/documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Documents))
    documents = result.scalars().all()
    return documents

@app.get("/documents/{documents_id}")
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Documents).where(Documents.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

# process pdf document endpoint
@app.post("/document/{document_id}/process")
async def process_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Documents).where(Documents.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=40, detail="Document not found")
    
    try:
        document.status = "processing"
        document.error_message = None
        await db.commit()
    
        if document.file_type == ".pdf":
            chunks = process_pdf_into_chunks(document.storage_path)
        elif document.file_type == ".csv":
            chunks = process_csv_into_chunks(document.storage_path)
        else:
            raise HTTPException(status_code=400, detail="Only PDF and CSV processing are supported right now")
    
        for index, chunk in enumerate(chunks, start=1):
            db_chunk = DocumentChunk(
                document_id=document.id,
                page_number=chunk.get("page_number", 0),
                chunk_index=index,
                text=chunk["text"],
                token_count=chunk["token_count"]
            )
            db.add(db_chunk)
        
        document.chunk_count = len(chunks)
        document.status = "ready"
        document.processed_at = datetime.now(timezone.utc)
        await db.commit()
    
        return {
            "document_id": document.id,
            "status": document.status,
            "chunk_token": document.chunk_count,
            "processed_at": document.processed_at
        }
    except Exception as e:
        document.status = "failed"
        document.error_message = str(e)
        await db.commit()
        raise
    
@app.get("/documents/{document_id}/chunks")
async def list_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index))
    chunks = result.scalars().all()
    return chunks

# embed all the chunks
@app.post("/document/{document_id}/embed")
async def embed_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    response = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index))
    chunks = response.scalars().all()
    
    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks found for this document")
    
    for chunk in chunks:
        embedding = create_embeddings(chunk.text)
        
        add_chunk_embedding(
            chunk_id=chunk.id,
            text=chunk.text,
            embedding=embedding,
            metadata={
                "document_id": chunk.document_id,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "source_type": "text_chunk"
            }
        )
    
    return {
        "document_id": document_id,
        "embedded_chunks": len(chunks)
    }
    
@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Documents).where(Documents.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not Found to delete")
    
    document_chunks = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id))
    chunks = document_chunks.scalars().all()
    
    document_assets = await db.execute(select(DocumentAsset).where(DocumentAsset.document_id == document_id))
    assets = document_assets.scalars().all()
    
    delete_document_embeddings(document_id)
    
    for asset in assets:
        asset_path = Path(asset.asset_path)
        if asset_path.exists():
            asset_path.unlink()
            
        await db.delete(asset)
        
    for chunk in chunks:
        await db.delete(chunk)
        
    await db.delete(document)
    await db.commit()
    
    return {
        "document_id": document_id,
        "message": "Document deleted successfully"
    }
    
    
@app.get("/retrieve")
async def retrieve_chunk(question: str, top_k: int = 5):
    question_embedding = create_embeddings(question)
    results = query_chunks(question_embedding=question_embedding, top_k=top_k)
    
    return results

# call llm for answer
@app.post("/chat")
async def chat(question: str, top_k: int = 5, document_id: Annotated[list[str] | None, Query()] = None):
    # get question embeddings
    question_embedding = create_embeddings(question)
    
    # get relevant chunks
    results = query_chunks(question_embedding, top_k, document_ids=document_id)
    
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    
    # create context for llm
    context_parts = []
    for doc, metadata in zip(documents, metadatas):
        context_parts.append(
            f"""
Source:
Document ID: {metadata["document_id"]}
Page: {metadata["page_number"]}
Source Type: {metadata.get("source_type", "unknown")}
Chunk: {metadata.get("chunk_index", "N/A")}

Text:
{doc}
"""
        )
    
    context = "".join(context_parts)
    answer = generate_answer(question, context)
    
    sources = []
    for doc, metadata in zip(documents, metadatas):
        source_type = metadata.get("source_type", "text_chunk")
        
        source = {
            "document_id": metadata["document_id"],
            "page_number": metadata["page_number"],
            "source_type": source_type,
            "preview": doc[:300]
        }
        
        if source_type == "text_chunk":
            source["chunk_index"] = metadata.get("chunk_index")

        elif source_type == "asset":
            asset_id = metadata.get("asset_id")
            source["asset_id"] = metadata.get("asset_id")
            source["asset_type"] = metadata.get("asset_type")
            source["asset_path"] = metadata.get("asset_path")
            source["image_url"] = f"/assets/{asset_id}"

        sources.append(source)
        
    unique_sources = []
    seen = set()
        
    for source in sources:
        key = (
            source.get("document_id"),
            source.get("page_number"),
            source.get("source_type"),
            source.get("chunk_index"),
            source.get("asset_id")
        )
        if key not in seen:
            seen.add(key)
            unique_sources.append(source)

    return {
        "question": question,
        "answer": answer,
        "sources": unique_sources
    }
    
@app.post("/documents/{document_id}/extract-images")
async def extract_document_images(document_id: str, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(Documents).where(Documents.id == document_id))
    
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.file_type != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF image extraction is supported right now")
    
    assets = extract_pdf_page_images(document.storage_path, document_id)
    
    for asset in assets:
        s3_key = f"document-assets/{document.id}/page-{asset["page_number"]}.png"
        upload_file_to_s3(filename=asset["asset_path"], key=s3_key)
        db_asset = DocumentAsset(
            document_id=document.id,
            page_number=asset["page_number"],
            asset_type=asset["asset_type"],
            asset_path=s3_key,
        )
        db.add(db_asset)
    await db.commit()
    
    return {
        "document_id": document_id,
        "extracted_assets": len(assets),
        "assets": assets
    }
    
@app.get("/documents/{document_id}/assets")
async def list_documeny_assets(document_id: str, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentAsset).where(DocumentAsset.document_id == document_id)
                              .order_by(DocumentAsset.page_number))
    
    assets = result.scalars().all()
    return assets

@app.post("/documents/{document_id}/ocr-assets")
async def ocr_document_assets(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentAsset).where(DocumentAsset.document_id == document_id).order_by(DocumentAsset.page_number))
    assets = result.scalars().all()
    
    if not assets:
        raise HTTPException(status_code=404, detail="No assets found for this document")
    
    updated_assets = []
    
    for asset in assets:
        ocr_text = extract_text_from_image(asset.asset_path)
        asset.caption = ocr_text
        updated_assets.append({
            "asset_id": asset.id,
            "page_number": asset.page_number,
            "caption_preview": asset.caption
        })
        
        await db.commit()
        
    return {
        "document_id": document_id,
        "ocr_assets": len(updated_assets),
        "assets": updated_assets
    }
    
@app.post("/dpcuments/{document_id}/embed-assets")
async def embed_document_assets(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentAsset).where(DocumentAsset.document_id == document_id).order_by(DocumentAsset.page_number))
    assets = result.scalars().all()
    
    if not assets:
        raise HTTPException(status_code=404, detail="Assets not found for this document")
    
    embedded_assets = []
    
    for asset in assets:
        if not asset.caption or not asset.caption.strip():
            continue
        
        embedding = create_embeddings(asset.caption)
        
        add_asset_embedding(asset_id=asset.id, text=asset.caption, embedding=embedding,
                            metadata={
                                "document_id": asset.document_id,
                                "asset_id": asset.id,
                                "page_number": asset.page_number,
                                "asset_type": asset.asset_type,
                                "asset_path": asset.asset_path,
                                "source_type": "asset"
                            })
        
        embedded_assets.append({
            "asset_id": asset.id,
            "page_number": asset.page_number,
            "asset_type": asset.asset_type
        })
    
    return {
        "document_id": document_id,
        "embedded_assets": len(embedded_assets),
        "assets": embedded_assets
    }
    
@app.get("/assets/{asset_id}")
async def get_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentAsset).where(DocumentAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    presigned_url = generate_presigned_URL(asset.asset_path)
    
    return {"asset_id": asset.id, "image_url": presigned_url}