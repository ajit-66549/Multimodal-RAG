# HPC Multimodal RAG Analyzer

A full-stack retrieval-augmented generation application for asking grounded questions about PDF and CSV documents. PDF pages are indexed as text and as OCR-enriched images, allowing answers to cite textual and visual evidence.

## Current capabilities

- Upload and process PDF and CSV files.
- Extract and token-chunk PDF text with page metadata.
- Build CSV overview, missing-value, numeric, categorical, and complete-row chunks.
- Render PDF pages as images, store them in Amazon S3, and caption them with Tesseract OCR.
- Generate OpenAI embeddings and persist them in a local ChromaDB collection.
- Store document, chunk, asset, and processing-status metadata in PostgreSQL.
- Ask questions against a selected ready document and display deduplicated sources.
- Remove a document and its local files, S3 assets, database records, and vectors.

The application does **not** currently process TXT or standalone image uploads. Authentication, background jobs, automated retries, and production cloud infrastructure are also outside the current implementation.

## Architecture

```text
React UI (browser)
  └── FastAPI API
        ├── PostgreSQL: document/chunk/asset metadata
        ├── local storage: uploads and persistent ChromaDB vectors
        ├── Amazon S3: extracted PDF page images
        ├── Tesseract: OCR of extracted images
        └── OpenAI API: embeddings and grounded answer generation
```

The detailed ingestion and retrieval flows are documented in [`docs/architecture.md`](docs/architecture.md).

## Technology stack

| Area | Technologies |
| --- | --- |
| Frontend | React 19, Vite 8, Axios, Nginx |
| API | FastAPI, Pydantic, Uvicorn |
| Persistence | PostgreSQL 16, SQLAlchemy, Alembic, ChromaDB |
| Document processing | PyPDF, PyMuPDF, pandas, Tesseract OCR |
| AI | OpenAI embeddings and chat completions |
| Assets | Amazon S3 and presigned URLs |
| Packaging | Docker and Docker Compose |

## Repository layout

```text
.
├── backend/
│   ├── app/                 # ingestion, storage, AI, and database services
│   ├── migrations/          # Alembic migration history
│   ├── .env.example         # required backend configuration template
│   ├── main.py              # FastAPI routes and pipeline orchestration
│   └── start.sh             # migrations followed by API startup
├── docs/architecture.md
├── frontend/
│   ├── src/                 # React application and API client
│   ├── Dockerfile           # Vite build and Nginx runtime
│   └── README.md            # frontend-specific development notes
└── docker-compose.yml
```

## Prerequisites

- Docker with the Compose plugin
- An OpenAI API key
- An S3 bucket and AWS credentials with access to the `document-assets/` prefix

Running the backend directly also requires Python 3.13, PostgreSQL, and the `tesseract` executable. Running the frontend directly requires Node.js 24.

## Configuration

Create the ignored runtime environment file from the committed template:

```bash
cp backend/.env.example backend/.env
```

Set these values in `backend/.env`:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI embeddings and answer generation |
| `AWS_REGION` | Region containing the S3 bucket |
| `AWS_S3_BUCKET` | Bucket used for extracted PDF page images |
| `AWS_ACCESS_KEY_ID` | Optional when another standard boto3 credential source is available |
| `AWS_SECRET_ACCESS_KEY` | Optional when another standard boto3 credential source is available |
| `AWS_SESSION_TOKEN` | Optional for temporary credentials |
| `CORS_ORIGINS` | Comma-separated browser origins allowed to call the API |

Docker Compose supplies the container-specific `DATABASE_URL`, so the template's localhost database URL is mainly for direct backend execution.

The S3 principal needs permission to list the asset prefix and read, write, and delete its objects. Adapt the bucket name below:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::YOUR_BUCKET",
      "Condition": {"StringLike": {"s3:prefix": ["document-assets/*"]}}
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET/document-assets/*"
    }
  ]
}
```

## Run with Docker Compose

```bash
docker compose up --build
```

This starts PostgreSQL, applies Alembic migrations, starts FastAPI, and serves the production frontend through Nginx.

- Frontend: <http://localhost:3000>
- API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>
- PostgreSQL: `localhost:5432`

Stop the application with `docker compose down`. Add `--volumes` only when you intentionally want to delete the PostgreSQL volume. Uploaded files and ChromaDB data are stored in the ignored repository-level `storage/` directory.

## Processing flow

1. Upload a PDF or CSV from the browser.
2. Select **Ingest**. The UI calls the processing and embedding endpoints in sequence.
3. For a PDF, processing also extracts and uploads page images; the UI then runs OCR and embeds the captions.
4. Select the ready document in the chat header and submit a question.
5. FastAPI embeds the question, filters ChromaDB retrieval to that document, asks the LLM using the retrieved context, and returns source metadata.

## Development checks

```bash
python -m compileall -q backend
cd frontend && npm run lint
cd frontend && npm run build
docker compose config
```

## Deployment readiness

The Docker images provide a reproducible application package, but the Compose file is a **local-development topology**, not a production deployment definition. Before internet-facing deployment:

- provide managed PostgreSQL and durable storage for uploads and ChromaDB, or replace ChromaDB with a managed vector store;
- inject secrets through the target platform instead of copying `.env` files into hosts or images;
- set `VITE_API_BASE_URL` to the public HTTPS API URL at frontend build time;
- configure the API's allowed CORS origins for the deployed frontend;
- place both services behind TLS and add authentication, authorization, request-size limits, and rate limiting;
- move ingestion/OCR/embedding work to background jobs for larger documents;
- add automated backend tests, integration tests, backups, monitoring, and a restore procedure.

These are deployment tasks rather than claims about the current local application. The current code and documentation now describe the same implemented file types and processing sequence.
