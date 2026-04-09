from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


KnowledgeLibraryScope = Literal["personal", "shared"]
KnowledgeSourceType = Literal["uploaded_file", "private_sample_repo"]
KnowledgeAttachmentSourceType = Literal["uploaded_file", "private_sample", "private_upload"]
KnowledgeParseStatus = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "pending_update",
    "pending",
    "parsed",
    "parse_failed",
]
KnowledgeIngestStatus = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "pending_update",
    "pending",
    "ingested",
    "ingest_failed",
]
KnowledgeIndexStatus = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "pending_update",
    "pending",
    "indexed",
    "index_failed",
    "stale",
]
KnowledgeTaskType = Literal["upload_ingest", "rebuild", "rescan", "retry"]
KnowledgeTaskStatus = Literal["queued", "running", "succeeded", "failed"]


class KnowledgeItemSummary(BaseModel):
    knowledge_item_id: str
    doc_id: str | None = None
    owner_user_id: str | None = None
    library_scope: KnowledgeLibraryScope
    source_type: KnowledgeSourceType
    title: str
    mime_type: str | None = None
    storage_path: str | None = None
    parse_status: KnowledgeParseStatus
    ingest_status: KnowledgeIngestStatus
    index_status: KnowledgeIndexStatus
    is_enabled: bool = True
    session_attachable: bool = True
    source_hash: str | None = None
    source_mtime: datetime | str | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
    last_indexed_at: datetime | None = None
    sample_type: str | None = None
    business_topic: str | None = None
    source: str | None = None
    source_url: str | None = None
    file_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _fill_doc_id(cls, values):
        if isinstance(values, dict) and not values.get("doc_id") and values.get("knowledge_item_id"):
            values = dict(values)
            values["doc_id"] = values["knowledge_item_id"]
        return values

    @model_validator(mode="after")
    def _ensure_doc_id(self):
        if not self.doc_id:
            self.doc_id = self.knowledge_item_id
        return self


class KnowledgeItemDetail(KnowledgeItemSummary):
    metadata: dict[str, str] = Field(default_factory=dict)
    chunk_count: int = 0
    task_count: int = 0


class KnowledgeChunkRecord(BaseModel):
    chunk_id: str
    knowledge_item_id: str
    title: str
    source_type: str
    library_scope: KnowledgeLibraryScope
    source: str
    source_url: str | None = None
    issued_at: str | None = None
    region: str | None = None
    doc_type: str | None = None
    sample_type: str | None = None
    business_topic: str | None = None
    snippet: str
    order_index: int
    created_at: datetime


class KnowledgeTaskSummary(BaseModel):
    task_id: str
    knowledge_item_id: str | None = None
    owner_user_id: str | None = None
    requested_by_user_id: str | None = None
    task_type: KnowledgeTaskType
    status: KnowledgeTaskStatus
    summary: str | None = None
    error_detail: str | None = None
    attempt_count: int = 0
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class KnowledgeItemCatalogFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    library_scope: KnowledgeLibraryScope | None = None
    source_type: KnowledgeSourceType | None = None
    parse_status: KnowledgeParseStatus | None = None
    ingest_status: KnowledgeIngestStatus | None = None
    index_status: KnowledgeIndexStatus | None = None
    session_attachable: bool | None = None
    is_enabled: bool | None = None
