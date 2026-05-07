from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.retrieval.schemas import RetrievedChunk, SourceType


DocumentSourceType = str
DocumentBlockType = Literal["title", "paragraph", "table", "list", "unknown"]
DocumentBlockKind = Literal["text", "heading", "table", "image", "formula", "page"]
RetrievalStrategyName = Literal["dense_only", "bm25_dense_hybrid", "citation_first", "graph_augmented"]
GovernanceVisibility = Literal["public", "tenant", "private", "demo"]


class DocumentBlock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    block_id: str
    document_id: str = ""
    block_type: DocumentBlockType = "paragraph"
    text: str
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    order_index: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_fields(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        if "block_type" not in data and "kind" in data:
            data["block_type"] = _normalize_block_type(data["kind"])
        if "page" not in data and "page_number" in data:
            data["page"] = data["page_number"]
        return data

    @property
    def kind(self) -> DocumentBlockKind:
        if self.block_type == "title":
            return "heading"
        if self.block_type == "paragraph":
            return "text"
        if self.block_type == "table":
            return "table"
        return "text"

    @property
    def page_number(self) -> int | None:
        return self.page


class ParsedDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: f"document-{uuid4().hex[:12]}")
    source_uri: str | None = None
    source_type: DocumentSourceType = "unknown"
    title: str | None = None
    blocks: list[DocumentBlock] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    text: str = ""
    mime_type: str | None = None
    source_path: str | None = None
    parser_name: str = "lightweight"
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    tenant_id: str | None = None
    owner_user_id: str | None = None
    visibility: GovernanceVisibility = "private"
    created_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context: Any) -> None:
        if self.source_uri is None and self.source_path is not None:
            self.source_uri = self.source_path
        if self.title is None and self.source_uri:
            self.title = self.source_uri.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]


class ChunkRecord(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    source_type: SourceType
    title: str
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    block_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    knowledge_item_id: str | None = None
    source: str | None = None
    source_uri: str | None = None
    source_url: str | None = None
    token_count: int = Field(default=0, ge=0)
    content_hash: str = ""
    tenant_id: str | None = None
    owner_user_id: str | None = None
    visibility: GovernanceVisibility = "private"
    created_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_chunk_fields(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        if "text" not in data and "snippet" in data:
            data["text"] = data["snippet"]
        if "source_uri" not in data and "source_url" in data:
            data["source_uri"] = data["source_url"]
        return data

    def model_post_init(self, __context: Any) -> None:
        if not self.content_hash:
            self.content_hash = hash_content(self.text)
        if self.token_count == 0 and self.text:
            self.token_count = _rough_token_count(self.text)

    @property
    def snippet(self) -> str:
        return self.text

    @classmethod
    def from_retrieved_chunk(cls, chunk: RetrievedChunk) -> "ChunkRecord":
        return cls(
            chunk_id=chunk.chunk_id,
            document_id=chunk.doc_id,
            text=chunk.snippet,
            source_type=chunk.source_type,
            title=chunk.title,
            page=None,
            section=chunk.region or chunk.doc_type,
            block_ids=[],
            knowledge_item_id=chunk.knowledge_item_id,
            source=chunk.source,
            source_uri=chunk.source_url,
            source_url=chunk.source_url,
            token_count=_rough_token_count(chunk.snippet),
            content_hash=hash_content(chunk.snippet),
            tenant_id=_optional_str(chunk.metadata.get("tenant_id")) if hasattr(chunk, "metadata") else None,
            owner_user_id=_optional_str(chunk.metadata.get("owner_user_id")) if hasattr(chunk, "metadata") else None,
            visibility=_normalize_visibility(chunk.library_scope),
            created_by=_optional_str(chunk.metadata.get("created_by")) if hasattr(chunk, "metadata") else None,
            metadata={
                "score": chunk.score,
                "issued_at": chunk.issued_at,
                "region": chunk.region,
                "doc_type": chunk.doc_type,
                "sample_type": chunk.sample_type,
                "business_topic": chunk.business_topic,
                "library_scope": chunk.library_scope,
            },
        )


class EmbeddingRecord(BaseModel):
    embedding_id: str = Field(default_factory=lambda: f"embedding-{uuid4().hex[:12]}")
    chunk_id: str
    model_name: str = "unknown"
    vector: list[float] = Field(default_factory=list)
    dimension: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_name: str | None = None
    vector_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str | None = None
    owner_user_id: str | None = None
    visibility: GovernanceVisibility = "private"
    created_by: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def normalize_embedding_fields(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        if "dimension" not in data and "dimensions" in data:
            data["dimension"] = data["dimensions"]
        return data

    def model_post_init(self, __context: Any) -> None:
        if self.dimension == 0 and self.vector:
            self.dimension = len(self.vector)
        if self.vector_hash is None and self.vector:
            self.vector_hash = hash_content(",".join(str(item) for item in self.vector))

    @property
    def dimensions(self) -> int:
        return self.dimension


class CitationRef(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    title: str
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    source_uri: str | None = None
    quote: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_type: SourceType | None = None
    source: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_citation_fields(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        if "citation_id" not in data and "reference_id" in data:
            data["citation_id"] = data["reference_id"]
        if "source_uri" not in data and "source_url" in data:
            data["source_uri"] = data["source_url"]
        return data

    @property
    def reference_id(self) -> str:
        return self.citation_id

    @property
    def source_url(self) -> str | None:
        return self.source_uri

    @classmethod
    def from_chunk_record(cls, *, reference_id: str, chunk: ChunkRecord) -> "CitationRef":
        return cls(
            citation_id=reference_id,
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            title=chunk.title,
            page=chunk.page,
            section=chunk.section,
            source_uri=chunk.source_uri or chunk.source_url,
            quote=chunk.text,
            metadata={**chunk.metadata, "knowledge_item_id": chunk.knowledge_item_id},
            source_type=chunk.source_type,
            source=chunk.source,
        )


class RetrievalTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: f"rag-trace-{uuid4().hex[:12]}")
    query: str | None = None
    retriever_mode: str | None = None
    requested_top_k: int | None = Field(default=None, ge=1)
    returned_count: int = Field(default=0, ge=0)
    fallback_used: bool = False
    fallback_reason: str | None = None
    chunk_ids: list[str] = Field(default_factory=list)
    citations: list[CitationRef] = Field(default_factory=list)
    strategy: RetrievalStrategyName = "bm25_dense_hybrid"
    retrieval_path: list[str] = Field(default_factory=list)
    latency_ms: float = Field(default=0.0, ge=0.0)
    total_hits: int = Field(default=0, ge=0)
    workflow_id: str | None = None
    parser_name: str | None = None
    vector_backend: str | None = None
    error_code: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.returned_count == 0 and self.total_hits:
            self.returned_count = self.total_hits
        if self.total_hits == 0 and self.returned_count:
            self.total_hits = self.returned_count
        if not self.chunk_ids and self.citations:
            self.chunk_ids = [citation.chunk_id for citation in self.citations]


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _rough_token_count(content: str) -> int:
    return len([part for part in content.replace("\n", " ").split(" ") if part.strip()])


def _normalize_block_type(value: Any) -> DocumentBlockType:
    mapping = {
        "heading": "title",
        "title": "title",
        "text": "paragraph",
        "paragraph": "paragraph",
        "table": "table",
        "list": "list",
        "unknown": "unknown",
    }
    return mapping.get(str(value), "unknown")  # type: ignore[return-value]


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _normalize_visibility(value: Any) -> GovernanceVisibility:
    if value in {"public", "tenant", "private", "demo"}:
        return value
    if value == "shared":
        return "demo"
    if value == "personal":
        return "private"
    return "private"
