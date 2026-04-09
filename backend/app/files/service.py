from pathlib import Path
from uuid import uuid4

from app.files.storage import FileStorage, get_file_storage
from app.session.schemas import UploadedFile
from app.session.service import SessionService, get_session_service

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".xls", ".xlsx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


class FileService:
    def __init__(
        self,
        *,
        session_service: SessionService | None = None,
        storage: FileStorage | None = None,
    ) -> None:
        self.session_service = session_service or get_session_service()
        self.storage = storage or get_file_storage()

    def validate_upload(self, *, filename: str, mime_type: str, size: int) -> None:
        suffix = Path(filename).suffix.lower()
        if size > MAX_UPLOAD_BYTES:
            raise ValueError("上传文件大小不能超过 20 MB。")
        if suffix not in ALLOWED_EXTENSIONS:
            raise TypeError("当前仅支持保守文档类附件上传。")
        if mime_type and mime_type not in ALLOWED_MIME_TYPES:
            raise TypeError("当前附件 MIME 类型不在允许范围内。")

    def save_upload(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> UploadedFile:
        self.session_service.require_session(owner_user_id=owner_user_id, session_id=session_id)
        self.validate_upload(filename=filename, mime_type=mime_type, size=len(content))
        file_id = f"file-{uuid4().hex[:12]}"
        storage_path = self.storage.save(
            session_id=session_id,
            file_id=file_id,
            filename=filename,
            content=content,
        )
        return self.session_service.record_uploaded_file(
            owner_user_id=owner_user_id,
            file_id=file_id,
            session_id=session_id,
            filename=filename,
            size=len(content),
            mime_type=mime_type or "application/octet-stream",
            storage_path=str(storage_path),
        )


def get_file_service() -> FileService:
    return FileService()
