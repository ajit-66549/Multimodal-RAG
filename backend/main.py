from fastapi import FastAPI

app = FastAPI(title="HPC Multimodal RAG Analyzer")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "hpc-rag-analyzer"
    }