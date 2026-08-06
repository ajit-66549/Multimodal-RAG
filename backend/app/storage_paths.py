from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORAGE_ROOT = PROJECT_ROOT / "storage"
UPLOAD_DIR = STORAGE_ROOT / "uploads"
ASSET_DIR = STORAGE_ROOT / "assets"
CHROMA_DIR = STORAGE_ROOT / "chroma_db"

for directory in (UPLOAD_DIR, ASSET_DIR, CHROMA_DIR):
    directory.mkdir(parents=True, exist_ok=True)