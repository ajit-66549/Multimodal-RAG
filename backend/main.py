from fastapi import FastAPI, File, UploadFile, HTTPException
from pathlib import Path
from uuid import uuid4

app = FastAPI(title="HPC Multimodal RAG Analyzer")

UPLOAD_DIR = Path("../storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".png", ".jpg", ".jpeg"}

# health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "hpc-rag-analyzer"
    }
    
# upload documents endpoint
@app.post("/documents/upload")
async def upload_documents(file: UploadFile = File(...)):
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
        
    return {
        "document_id": document_id,
        "filename": original_name,
        "saved_as": saved_name,
        "file_type": file_ext,
        "status": "uploaded"
    }