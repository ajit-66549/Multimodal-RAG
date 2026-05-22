from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pathlib import Path
from uuid import uuid4
from contextlib import asynccontextmanager

from app.database import Base, engine, get_db
from app.models import Documents
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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