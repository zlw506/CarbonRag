from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.memory.schemas import MemoryState
from app.schemas.ask import AskCitation, AskSourceSummary, KnowledgeScope, MessageStatus

MessageRole = Literal["user", "assistant", "system"]
AttachmentSourceType = Literal["uploaded_file", "private_sample"]


class SessionMessage(BaseModel):
    message_id: str
    role: MessageRole
    content: str
    thinking_content: str | None = None
    created_at: datetime
    status: MessageStatus | None = None
    trace_id: str | None = None
    citations: list[AskCitation] = Field(default_factory=list)


class UploadedFile(BaseModel):
    file_id: str
    session_id: str
    filename: str
    size: int
    mime_type: str
    stored_at: datetime
    storage_path: str | None = None
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
    updated_at: datetime | None = None
    summary: str | None = None
    chunk_count: int = 0
    knowledge_item_id: str | None = None


class SessionAttachment(BaseModel):
    file_id: str
    knowledge_item_id: str | None = None
    filename: str
    source_type: AttachmentSourceType
    attached_at: datetime
    parse_status: str | None = None
    index_status: str | None = None
    summary: str | None = None
    page_count: int | None = None
    sheet_count: int | None = None
    slide_count: int | None = None
    chunk_count: int | None = None
    error_message: str | None = None


class SessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    pinned_at: datetime | None = None
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
    memory_state: MemoryState | None = None


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

    title: str | None = None
    is_pinned: bool | None = None

    @field_validator("title")
    @classmethod
    def require_non_empty_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("会话标题不能为空。")
        return normalized


class BulkDeleteSessionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_ids: list[str] = Field(min_length=1, max_length=100)

    @field_validator("session_ids")
    @classmethod
    def normalize_session_ids(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            session_id = str(item).strip()
            if not session_id or session_id in seen:
                continue
            seen.add(session_id)
            normalized.append(session_id)
        if not normalized:
            raise ValueError("至少需要选择一个会话。")
        return normalized


class BulkDeleteSessionsResponse(BaseModel):
    deleted_count: int
    deleted_session_ids: list[str] = Field(default_factory=list)
    missing_session_ids: list[str] = Field(default_factory=list)


class ReplaceAttachedPrivateSamplesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_ids: list[str] = Field(default_factory=list)
    knowledge_item_ids: list[str] = Field(default_factory=list)
