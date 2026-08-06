# HPC Multimodal RAG frontend

The React/Vite interface uploads PDF and CSV documents, starts their ingestion pipeline, and asks questions against one ready document at a time. PDF ingestion includes page-image extraction, OCR, and visual-source retrieval.

<<<<<<< ours
<<<<<<< ours
# Local development
```bash
npm ci
npm run dev
```
=======
=======
>>>>>>> theirs
## Local development

```bash
npm ci
npm run dev
```

The frontend uses `VITE_API_BASE_URL` when it is set and otherwise connects to `http://127.0.0.1:8000`. The full application and its production Nginx build can be started from the repository root with Docker Compose; see the root `README.md` for configuration.

## Checks

```bash
npm run lint
npm run build
```
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
