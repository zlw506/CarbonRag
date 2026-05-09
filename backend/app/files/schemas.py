from datetime import datetime

from pydantic import BaseModel


class UploadedFileResponse(BaseModel):
    file_id: str
    session_id: str
    filename: str
    size: int
    mime_type: str
    stored_at: datetime
    stored_filename: str | None = None
    file_ext: str | None = None
    sha256: str | None = None
    parse_status: str = "uploaded"
    parser_name: str | None = None
    parser_version: str | None = None
    ocr_used: bool = False
    page_count: int | None = None
    sheet_count: int | None = None
    slide_count: int | None = None
    error_message: str | None = None
    summary: str | None = None
    chunk_count: int = 0
    knowledge_item_id: str | None = None
