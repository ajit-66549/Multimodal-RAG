# HPC Multimodal RAG Analyzer

A full-stack AI application that extracts knowledge from technical documents using **Multimodal Retrieval-Augmented Generation (RAG)**. The system processes both textual and visual content by combining OCR, semantic vector search, Amazon S3, ChromaDB, and Large Language Models to generate grounded answers with supporting sources.

---

## Overview

Traditional RAG systems primarily retrieve information from document text while ignoring valuable information contained in figures, diagrams, and images.

The **HPC Multimodal RAG Analyzer** extends a standard RAG pipeline by processing both textual and visual content from uploaded documents. During ingestion, the application extracts document text, captures embedded images, generates OCR captions, stores visual assets securely in Amazon S3, creates vector embeddings, and indexes all content in ChromaDB for semantic retrieval.

When a user asks a question, the system retrieves the most relevant document chunks, grounds the response with supporting evidence, and displays both textual and visual sources whenever applicable.

---

# Features

- Upload PDF, CSV, and TXT documents
- Extract text and embedded images from PDF files
- Generate OCR captions for visual content
- Store extracted assets securely in Amazon S3
- Generate semantic embeddings for document chunks
- Store vector embeddings in ChromaDB
- Ask natural language questions about uploaded documents
- Retrieve grounded answers with supporting sources
- Display both text and image references
- Dockerized frontend, backend, and PostgreSQL
- Automatic Alembic database migrations during container startup
- One-command project startup using Docker Compose

---

# System Architecture

User Upload → FastAPI → PostgreSQL + Local Document Storage + S3 Asset Storage → Text/CSV/Image Processing → Embeddings → ChromaDB → Retrieval → LLM Answer

---

# Tech Stack

## Frontend

- React
- Vite
- JavaScript
- CSS

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

## Database

- PostgreSQL

## Vector Database

- ChromaDB

## AI

- OpenAI API
- Retrieval-Augmented Generation (RAG)
- OCR

## Cloud

- Amazon S3
- Presigned URLs

## DevOps

- Docker
- Docker Compose

---

## S3 configuration

Set `AWS_REGION` and `AWS_S3_BUCKET` in `backend/.env`. Boto3 uses its standard
credential chain, so local development can also set `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` (and `AWS_SESSION_TOKEN` for temporary credentials).

The application uploads, reads, and deletes objects below the
`document-assets/` prefix. Its IAM principal therefore needs this policy (replace
the bucket name if necessary):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListDocumentAssets",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::hpc-rag-assets",
      "Condition": {
        "StringLike": { "s3:prefix": ["document-assets/*"] }
      }
    },
    {
      "Sid": "ManageDocumentAssets",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::hpc-rag-assets/document-assets/*"
    }
  ]
}
```

The AWS account number in a user ARN identifies its account, but does not grant
S3 permissions. Attach an identity policy like the one above to the IAM user or
role, and also check the bucket policy, permissions boundary, and organization
SCP for an explicit deny. A missing object can appear as HTTP 403 rather than 404
when the principal lacks `s3:ListBucket`; verify that database `asset_path`
values begin with `document-assets/`.

---

# Project Structure

```
hpc-rag-analyzer/

├── backend/
│   ├── app/
│   ├── migrations/
│   ├── main.py
│   ├── start.sh
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── docker-compose.yml
│
└── README.md
```

---

# How It Works

### 1. Upload

The user uploads a supported document.

Supported formats:

- PDF
- CSV
- TXT

---

### 2. Document Processing

The backend:

- extracts document text
- extracts embedded images
- generates OCR captions
- stores image assets in Amazon S3
- chunks document text
- generates vector embeddings
- stores vectors in ChromaDB
- stores metadata in PostgreSQL

---

### 3. Retrieval

When the user submits a question:

- the question is embedded
- similar document chunks are retrieved from ChromaDB
- relevant sources are collected
- visual references are retrieved from S3 when available

---

### 4. Answer Generation

The retrieved context is sent to the LLM to generate a grounded response.

The application displays:

- answer
- source pages
- supporting document chunks
- related images (when available)

---

# Getting Started

## Clone the repository

```bash
git clone https://github.com/<your-username>/hpc-rag-analyzer.git

cd hpc-rag-analyzer
```

---

## Configure Environment Variables

Create:

```
backend/.env
```

Example:

```env
OPENAI_API_KEY=your_openai_api_key

DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/hpc_rag_db

AWS_ACCESS_KEY_ID=your_access_key

AWS_SECRET_ACCESS_KEY=your_secret_key

AWS_REGION=your_region

AWS_S3_BUCKET=your_bucket_name
```

---

## Run the Entire Application

```bash
docker compose up --build
```

Docker Compose automatically:

- starts PostgreSQL
- waits for the database
- runs Alembic migrations
- starts the FastAPI backend
- builds the React frontend

---

Frontend:

```
http://localhost:5173
```

Backend:

```
http://localhost:8000
```

API Documentation:

```
http://localhost:8000/docs
```

---

# Example Workflow

1. Upload a PDF document.
2. Process the document.
3. Ask a question.

Example:

```
What is Retrieval-Augmented Generation?
```

The system retrieves the most relevant document chunks, generates an answer using the LLM, and displays the supporting sources.

---

# Dockerized Deployment

The entire project is containerized.

A single command launches:

- React frontend
- FastAPI backend
- PostgreSQL database

Database migrations are automatically executed during container startup using Alembic.

---

# Future Improvements

- Multi-document querying
- Streaming LLM responses
- User authentication
- Conversation history
- Citation highlighting
- Hybrid keyword + semantic retrieval
- Document summarization
- Multi-user support

---

# Learning Outcomes

This project demonstrates experience with:

- Full-stack application development
- Retrieval-Augmented Generation (RAG)
- FastAPI
- React
- PostgreSQL
- Alembic migrations
- ChromaDB
- Amazon S3
- Docker
- Docker Compose
- Semantic search
- OCR
- Cloud storage
- REST APIs

---

## 📸 Application Preview

### Upload, Process, and Ask Questions

The application allows users to upload technical documents, automatically extract text and visual assets, and ask grounded questions over the processed knowledge base.

![Home Dashboard](docs/images/home-dashboard.png)

---

### Grounded Responses with Citations

Every answer includes traceable citations from indexed document chunks and extracted visual assets, helping users verify where the information originated.

![Pipeline and Answer](docs/images/pipeline-answer.png)

# License

This project is licensed under the MIT License.