import fitz

from uuid import uuid4
from app.storage_paths import ASSET_DIR

def extract_pdf_page_images(file_path: str, document_id: str):
    pdf = fitz.open(file_path)
    
    assets = []
    
    for page_index in range(len(pdf)):
        page = pdf[page_index]
        
        pix = page.get_pixmap(dpi=150)
        image_id = str(uuid4())
        image_name = f"{document_id}_page_{page_index+1}_{image_id}.png"
        image_path = ASSET_DIR / image_name
        
        pix.save(image_path)
        
        assets.append({
            "page_number": page_index + 1,
            "asset_type": "page_image",
            "asset_path": str(image_path)
        })
        
    pdf.close()
    
    return assets

def delete_extracted_images(document_id: str) -> int:
    """Delete locally generated page images for a document."""
    deleted_count = 0
    for image_path in ASSET_DIR.glob(f"{document_id}_page_*.png"):
        if image_path.is_file():
            image_path.unlink()
            deleted_count += 1

    return deleted_count