import tiktoken
from pypdf import PdfReader
from pathlib import Path

def extract_pdf_text_by_page(file_path: str):
    reader = PdfReader(file_path)
    pages = []
    
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({
                "page_number": page_index,
                "text": text
            })
    return pages

def chunk_text_by_tokens(text: str, chunk_size: int = 150, overlap: int = 20):
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        
        chunks.append({
            "text": chunk_text,
            "token_count": len(chunk_tokens)
        })
        start = end - overlap
    return chunks

def process_pdf_into_chunks(file_path: str):
    pages = extract_pdf_text_by_page(file_path)
    all_chunks = []
    
    for page in pages:
        page_chunks = chunk_text_by_tokens(page["text"])
        
        for chunk in page_chunks:
            all_chunks.append({
                "page_number": page["page_number"],
                "text": chunk["text"],
                "token_count": chunk["token_count"]
            })
    return all_chunks