import re
from functools import lru_cache
from pathlib import Path

from app.core.config import REPO_ROOT, get_settings


def resolve_upload_root(upload_root: Path | str | None = None) -> Path:
    raw_path = Path(upload_root or get_settings().upload_dir)
    return raw_path if raw_path.is_absolute() else REPO_ROOT / raw_path


def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
    return sanitized or "upload.bin"


class FileStorage:
    def __init__(self, upload_root: Path | str | None = None) -> None:
        self.upload_root = resolve_upload_root(upload_root)
        self.upload_root.mkdir(parents=True, exist_ok=True)

    def save(self, *, session_id: str, file_id: str, filename: str, content: bytes) -> Path:
        target_dir = self.upload_root / session_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{file_id}__{sanitize_filename(filename)}"
        target_path.write_bytes(content)
        return target_path


@lru_cache(maxsize=1)
def get_file_storage() -> FileStorage:
    return FileStorage()
