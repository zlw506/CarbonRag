from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ask import AskCitation, AskSourceSummary, AskStatus, KnowledgeScope

MessageRole = Literal["user", "assistant", "system"]
AttachmentSourceType = Literal["uploaded_file", "private_sample"]


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


class SessionAttachment(BaseModel):
    file_id: str
    knowledge_item_id: str | None = None
    filename: str
    source_type: AttachmentSourceType
    attached_at: datetime


class SessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    file_count: int = 0
    attached_private_sample_count: int = 0
    attached_knowledge_item_count: int = 0


class SessionDetail(SessionSummary):
    messages: list[SessionMessage] = Field(default_factory=list)
    files: list[UploadedFile] = Field(default_factory=list)
    attached_files: list[SessionAttachment] = Field(default_factory=list)
    knowledge_scope_last_used: KnowledgeScope | None = None
    source_summary: AskSourceSummary | None = None


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


class ReplaceAttachedPrivateSamplesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_ids: list[str] = Field(default_factory=list)
    knowledge_item_ids: list[str] = Field(default_factory=list)
