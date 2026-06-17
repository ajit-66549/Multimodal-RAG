                          +----------------------+
                          |      React UI        |
                          | Upload • Chat • Docs |
                          +----------+-----------+
                                     |
                                     |
                                     v
                         +-----------------------+
                         |     FastAPI API       |
                         +-----------------------+
                          |        |         |
                          |        |         |
                          v        v         v
                 PostgreSQL   Local Storage  ChromaDB
               (metadata)    (PDF/CSV/Image) (vectors)
                          |                   ^
                          |                   |
                          v                   |
                 PDF / CSV Processing         |
                 OCR + Image Extraction       |
                 Chunking + Embeddings -------+
                          |
                          v
                    OpenAI Embeddings
                          |
                          v
                    OpenAI Chat Model
                          |
                          v
                 Grounded Answer + Sources