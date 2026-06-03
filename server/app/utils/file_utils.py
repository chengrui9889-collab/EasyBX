import uuid
from pathlib import Path


def generate_storage_path(upload_dir: Path, user_id: int, original_filename: str) -> str:
    unique_name = f"{uuid.uuid4().hex}_{original_filename}"
    user_dir = upload_dir / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return str(user_dir / unique_name)


ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}


def is_allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS
