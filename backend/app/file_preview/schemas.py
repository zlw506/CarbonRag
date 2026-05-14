from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

FilePreviewSourceType = Literal["session_file", "rag_document", "crawler_candidate", "knowledge_item"]


class FilePreviewChunk(BaseModel):
    chunk_id: str
    doc_id: str | None = None
    kb_id: str | None = None
    order_index: int = 0
    text: str
    title: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    page_number: int | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
    section_title: str | None = None
    vector_status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FilePreviewResponse(BaseModel):
    source_type: FilePreviewSourceType
    source_id: str
    title: str
    filename: str | None = None
    mime_type: str | None = None
    size: int | None = None
    status: str
    source_url: str | None = None
    markdown: str | None = None
    text: str | None = None
    chunks: list[FilePreviewChunk] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_available: bool = False
    raw_preview_url: str | None = None
    raw_download_url: str | None = None
    can_inline_raw: bool = False
    available_tabs: list[str] = Field(default_factory=list)
    truncated: bool = False
