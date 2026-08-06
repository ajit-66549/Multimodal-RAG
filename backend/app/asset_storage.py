from pathlib import Path
from app.s3_service import delete_s3_object, upload_file_to_s3

def upload_extracted_assets(document_id: str, assets: list[dict]) -> list[dict]:
    """Upload extracted page images and replace local paths with S3 object keys."""
    stored_assets = []
    uploaded_keys = []

    try:
        for asset in assets:
            key = f"document-assets/{document_id}/page-{asset['page_number']}.png"
            upload_file_to_s3(filename=asset["asset_path"], key=key)
            uploaded_keys.append(key)
            stored_assets.append({**asset, "asset_path": key})
    except Exception:
        for key in uploaded_keys:
            try:
                delete_s3_object(key)
            except Exception:
                # Preserve the original upload error if rollback is not permitted.
                pass
        raise
    finally:
        for asset in assets:
            Path(asset["asset_path"]).unlink(missing_ok=True)

    return stored_assets