from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ask import AskCitation, AskStatus

MessageRole = Literal["user", "assistant"]


class SessionMessage(BaseModel):
    message_id: str
    role: MessageRole
    content: str
    created_at: datetime
    status: AskStatus | None = None
    trace_id: str | None = None
    citations: list[AskCitation] = Field(default_factory=list)


class UploadedFile(BaseModel):
    file_id: str
    session_id: str
    filename: str
    size: int
    mime_type: str
    stored_at: datetime


class SessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    file_count: int = 0


class SessionDetail(SessionSummary):
    messages: list[SessionMessage] = Field(default_factory=list)
    files: list[UploadedFile] = Field(default_factory=list)


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class UpdateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str

    @field_validator("title")
    @classmethod
    def require_non_empty_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("会话标题不能为空。")
        return normalized
