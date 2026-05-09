import hashlib
from pathlib import Path
from uuid import uuid4

from app.files.storage import FileStorage, get_file_storage
from app.knowledge import get_knowledge_service
from app.session.schemas import UploadedFile
from app.session.service import SessionService, get_session_service

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx", ".html", ".pptx", ".png", ".jpg", ".jpeg"}
BLOCKED_EXTENSIONS = {".exe", ".sh", ".bat", ".ps1", ".js", ".msi", ".zip", ".rar", ".7z", ".py", ".php", ".jsp", ".doc", ".docm", ".xls", ".xlsm", ".pptm"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/html",
    "image/png",
    "image/jpeg",
    "application/octet-stream",
}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_SESSION_FILES = 10
MAX_USER_UPLOAD_BYTES = 200 * 1024 * 1024


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
        if suffix in BLOCKED_EXTENSIONS:
            raise TypeError("该文件格式存在安全风险或暂不支持解析。")
        if suffix not in ALLOWED_EXTENSIONS:
            raise TypeError("当前仅支持 PDF、Office Open XML、CSV、文本、HTML 和常见图片附件。")
        if mime_type and mime_type not in ALLOWED_MIME_TYPES:
            raise TypeError("当前附件 MIME 类型不在允许范围内。")

    def validate_quota(self, *, owner_user_id: str, session_id: str, size: int) -> None:
        session = self.session_service.require_session(owner_user_id=owner_user_id, session_id=session_id)
        if len(session.files) >= MAX_SESSION_FILES:
            raise ValueError(f"单个会话最多上传 {MAX_SESSION_FILES} 个文件。")
        uploaded_total = sum(
            int(row.get("size") or 0)
            for row in get_knowledge_service().store.list_uploaded_files(owner_user_id=owner_user_id)
        )
        if uploaded_total + size > MAX_USER_UPLOAD_BYTES:
            raise ValueError("单个用户本地上传空间暂限制为 200 MB。")

    def save_upload(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> UploadedFile:
        self.validate_upload(filename=filename, mime_type=mime_type, size=len(content))
        self.validate_quota(owner_user_id=owner_user_id, session_id=session_id, size=len(content))
        file_id = f"file-{uuid4().hex[:12]}"
        file_ext = Path(filename).suffix.lower()
        stored_filename = f"{file_id}{file_ext}"
        sha256 = hashlib.sha256(content).hexdigest()
        storage_path = self.storage.save(
            session_id=session_id,
            file_id=file_id,
            file_ext=file_ext,
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
            stored_filename=stored_filename,
            file_ext=file_ext,
            sha256=sha256,
        )

    def get_upload_detail(self, *, owner_user_id: str, file_id: str) -> UploadedFile | None:
        row = get_knowledge_service().store.get_uploaded_file_detail(owner_user_id=owner_user_id, file_id=file_id)
        if row is None:
            return None
        return UploadedFile.model_validate(row)


def get_file_service() -> FileService:
    return FileService()
