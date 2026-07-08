# HPC Multimodal RAG Analyzer

Multimodal RAG platform for analyzing HPC research papers, performance charts, architecture diagrams, and workload datasets.

## Features

- Upload PDF and CSV documents
- Extract and chunk PDF text
- Generate CSV workload summaries
- Extract PDF page images
- Run OCR on extracted images
- Embed text chunks and OCR captions
- Retrieve text and image-based sources from ChromaDB
- Generate grounded answers using retrieved context
- Return source previews, page numbers, and image URLs

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- ChromaDB
- OpenAI Embeddings
- OpenAI Chat Model
- PyMuPDF
- Tesseract OCR
- pandas

## Architecture

User Upload → FastAPI → PostgreSQL + Local Storage → Text/CSV/Image Processing → Embeddings → ChromaDB → Retrieval → LLM Answer

## Current Status

Completed:

- PDF ingestion
- CSV ingestion
- OCR-based image ingestion
- Multimodal retrieval
- Source-grounded chat
- Document filtering
- Asset serving
- Delete document endpoint
- Alembic migrations

## API Endpoints

- `GET /health`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /documents/{document_id}/process`
- `POST /documents/{document_id}/embed`
- `POST /documents/{document_id}/extract-images`
- `POST /documents/{document_id}/ocr-assets`
- `POST /documents/{document_id}/embed-assets`
- `GET /documents/{document_id}/chunks`
- `GET /documents/{document_id}/assets`
- `GET /assets/{asset_id}`
- `POST /chat`
- `DELETE /documents/{document_id}`

## Known Limitations

- Processing is currently synchronous
- OCR quality depends on image clarity
- Uses local file storage instead of S3
- Frontend is not polished yet
- No user authentication yet

## Future Work

- Celery + Redis background processing
- React dashboard
- Chat history
- S3 asset storage
- Retrieval analytics