from datetime import datetime

from pydantic import BaseModel


class UploadedFileResponse(BaseModel):
    file_id: str
    session_id: str
    filename: str
    size: int
    mime_type: str
    stored_at: datetime
