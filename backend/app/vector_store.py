import chromadb
from app.storage_paths import CHROMA_DIR

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_or_create_collection(name="hpc_document_chunks")

def add_chunk_embedding(chunk_id: int, text: str, embedding: list[float], metadata: dict):
    collection.add(
        ids=[str(chunk_id)],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata]
    )

def query_chunks(question_embedding: list[float], top_k: int = 5, document_ids: list[str] | None=None):
    where_filter = None
    
    if document_ids:
        where_filter = {
            "document_id": {
                "$in": document_ids
            }
        }
    
    return collection.query(
        query_embeddings=question_embedding,
        n_results=top_k,
        where=where_filter
    )
    
def add_asset_embedding(asset_id: str, text: str, embedding: list[float], metadata: dict):
    collection.add(
        ids=[asset_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata]
    )
    
def delete_document_embeddings(document_id: str):
    collection.delete(where={"document_id": document_id})