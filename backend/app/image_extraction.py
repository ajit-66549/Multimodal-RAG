import fitz

from pathlib import Path
from uuid import uuid4

ASSET_DIR = Path("../storage/assets")
ASSET_DIR.mkdir(parents=True, exist_ok=True)

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