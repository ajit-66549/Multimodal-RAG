from uuid import uuid4
from pathlib import Path
from sqlalchemy import select
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends

from app.database import Base, engine, get_db
from app.models import Documents, DocumentChunk
from app.ingestion import process_pdf_into_chunks

UPLOAD_DIR = Path("../storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".png", ".jpg", ".jpeg"}
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    
app = FastAPI(title="HPC Multimodal RAG Analyzer", lifespan=lifespan)
    
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

# process pdf document endpoint
@app.post("/document/{document_id}/process")
async def process_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Documents).where(Documents.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=40, detail="Document not found")
    
    if document.file_type != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF processing is supported right now")
    
    document.status = "processing"
    db.commit()
    
    chunks = process_pdf_into_chunks(document.storage_path)
    
    for index, chunk in enumerate(chunks, start=1):
        db_chunk = DocumentChunk(
            document_id=document.id,
            page_number=chunk["page_number"],
            chunk_index=index,
            text=chunk["text"],
            token_count=chunk["token_count"]
        )
        db.add(db_chunk)
        
    document.chunk_count = len(chunks)
    document.status = "ready"
    await db.commit()
    
    return {
        "document_id": document.id,
        "status": document.status,
        "chunk_token": document.chunk_count
    }
    
@app.get("/documents/{document_id}/chunks")
async def list_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index))
    chunks = result.scalars().all()
    return chunks