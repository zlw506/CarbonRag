from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CompactionStatus = Literal["idle", "compacted", "failed"]


class MemoryState(BaseModel):
    context_usage_estimate: int = 0
    context_budget_estimate: int = 258_000
    summary_present: bool = False
    summary_updated_at: datetime | None = None
    compacted_message_count: int = 0
    compaction_status: CompactionStatus = "idle"
    summary_estimated_tokens: int = 0


class MemoryNote(BaseModel):
    memory_note_id: str
    owner_user_id: str
    title: str
    content: str
    is_enabled: bool = True
    created_at: datetime
    updated_at: datetime


class CreateMemoryNoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    content: str
    is_enabled: bool = True

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("记忆标题不能为空。")
        if len(normalized) > 80:
            raise ValueError("记忆标题不能超过 80 个字符。")
        return normalized

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("记忆内容不能为空。")
        if len(normalized) > 3_000:
            raise ValueError("记忆内容不能超过 3000 个字符。")
        return normalized


class UpdateMemoryNoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    content: str | None = None
    is_enabled: bool | None = None

    @field_validator("title")
    @classmethod
    def normalize_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("记忆标题不能为空。")
        if len(normalized) > 80:
            raise ValueError("记忆标题不能超过 80 个字符。")
        return normalized

    @field_validator("content")
    @classmethod
    def normalize_optional_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("记忆内容不能为空。")
        if len(normalized) > 3_000:
            raise ValueError("记忆内容不能超过 3000 个字符。")
        return normalized


class MemoryNoteCollection(BaseModel):
    notes: list[MemoryNote] = Field(default_factory=list)


class SessionMemoryMessage(BaseModel):
    message_seq: int
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime


class SessionMemorySnapshot(BaseModel):
    session_id: str
    owner_user_id: str
    session_summary: str | None = None
    summary_message_seq_upto: int | None = None
    summary_updated_at: datetime | None = None
    summary_estimated_tokens: int = 0
    compaction_status: CompactionStatus = "idle"
    last_compaction_error: str | None = None
    messages: list[SessionMemoryMessage] = Field(default_factory=list)


class SessionMemoryBundle(BaseModel):
    recent_messages: list[dict[str, str]] = Field(default_factory=list)
    session_summary: str | None = None
    memory_notes: list[MemoryNote] = Field(default_factory=list)
    context_usage_estimate: int = 0
    context_budget_estimate: int = 258_000
    compacted_message_count: int = 0
    compaction_status: CompactionStatus = "idle"
    summary_updated_at: datetime | None = None
    summary_present: bool = False
    summary_estimated_tokens: int = 0
