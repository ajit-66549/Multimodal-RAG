                         +----------------------+
                         |      React UI        |
                         | Upload • Chat • Docs |
                         +----------+-----------+
                                    |
                                    v
                         +-----------------------+
                         |     FastAPI API       |
                         +-----------------------+
                          |          |          |
                          |          |          |
                          v          v          v
                 PostgreSQL   Local Document   S3 Asset
                 (metadata)     Storage        Storage
                               (uploads)     (extracted
                                              images)
                          |          |          |
                          |          v          |
                          |  Text / CSV / Image  |
                          |  Processing + OCR    |
                          |  Chunking            |
                          |          |          |
                          |          v          |
                          |    Embeddings       |
                          |          |          |
                          +--------->+----------+
                                     |
                                     v
                                  ChromaDB
                                  (vectors)
                                     |
                                     v
                              Retrieval + RAG
                                     |
                                     v
                               LLM Answer
                                     |
                                     v
                         Grounded Answer + Sources

## Current Flow

1. User uploads a document through the React UI.
2. FastAPI stores the file locally and saves metadata in PostgreSQL.
3. PDF uploads also generate extracted page images, which are uploaded to S3 and tracked in the database.
4. Text, CSV, and image content is processed into chunks or OCR text.
5. Embeddings are created for the processed content and stored in ChromaDB.
6. Retrieval uses ChromaDB to fetch relevant chunks for a question.
7. The LLM generates a grounded answer with source references.