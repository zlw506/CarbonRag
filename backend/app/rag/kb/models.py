from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


KnowledgeBaseVisibility = Literal["private", "shared", "public"]
RagDocumentStatus = Literal["uploaded", "parsed", "chunked", "indexed", "failed"]
RagRetrievalMode = Literal["dense", "sparse", "hybrid", "hybrid_rerank"]


class KnowledgeBase(BaseModel):
    kb_id: str
    owner_user_id: str | None = None
    name: str
    description: str | None = None
    visibility: KnowledgeBaseVisibility = "private"
    retrieval_mode: RagRetrievalMode = "hybrid"
    is_default: bool = False
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagDocument(BaseModel):
    doc_id: str
    kb_id: str
    owner_user_id: str | None = None
    knowledge_item_id: str | None = None
    file_id: str | None = None
    title: str
    source_type: str
    status: RagDocumentStatus = "uploaded"
    parse_status: str = "uploaded"
    chunk_status: str = "pending"
    index_status: str = "pending"
    chunk_count: int = 0
    indexed_chunk_count: int = 0
    error_message: str | None = None
    vector_backend: str | None = None
    degraded: bool = False
    index_warnings: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagChunk(BaseModel):
    rag_chunk_id: str
    kb_id: str
    doc_id: str
    owner_user_id: str | None = None
    knowledge_chunk_id: str | None = None
    parent_chunk_id: str | None = None
    chunk_index: int
    text: str
    token_estimate: int = 0
    page_number: int | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
    section_title: str | None = None
    status: str = "chunked"
    vector_status: str = "pending"
    dense_vector: list[float] | None = None
    sparse_vector: dict[str, float] | None = None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    visibility: KnowledgeBaseVisibility = "private"
    retrieval_mode: RagRetrievalMode = "hybrid"

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name cannot be blank")
        return normalized


class KnowledgeBaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    visibility: KnowledgeBaseVisibility | None = None
    retrieval_mode: RagRetrievalMode | None = None


class RagDocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_item_id: str | None = None
    file_id: str | None = None
    title: str | None = None
    text: str | None = None
    source_type: str = "manual"


class RagSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    kb_id: str | None = None
    knowledge_scope: Literal["public", "private_sample", "mixed"] = "mixed"
    mode: RagRetrievalMode = "hybrid_rerank"
    top_k: int = Field(default=5, ge=1, le=50)
    allowed_knowledge_item_ids: list[str] = Field(default_factory=list)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("query cannot be blank")
        return normalized


class RagHit(BaseModel):
    chunk_id: str
    rag_chunk_id: str | None = None
    doc_id: str
    kb_id: str | None = None
    title: str
    snippet: str
    source_type: str
    source: str | None = None
    source_url: str | None = None
    library_scope: Literal["personal", "shared"] | None = None
    file_id: str | None = None
    knowledge_item_id: str | None = None
    page_number: int | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
    section_title: str | None = None
    dense_score: float | None = None
    sparse_score: float | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None

    @property
    def score(self) -> float:
        return self.rerank_score or self.rrf_score or self.dense_score or self.sparse_score or 0.0

    def to_tool_hit(self) -> dict[str, Any]:
        payload = self.model_dump()
        payload["score"] = self.score
        payload["bm25_score"] = self.sparse_score
        payload["vector_score"] = self.dense_score
        return payload


class RagTrace(BaseModel):
    dense_count: int = 0
    sparse_count: int = 0
    merged_count: int = 0
    rerank_applied: bool = False
    vector_backend: str = "memory"
    vector_runtime: str = "memory_dev"
    degraded: bool = False
    warnings: list[str] = Field(default_factory=list)
    retrieval_mode: RagRetrievalMode = "hybrid_rerank"
    kb_id: str | None = None
    knowledge_scope: str = "mixed"


class RagSearchResult(BaseModel):
    query: str
    kb_id: str | None = None
    hits: list[RagHit] = Field(default_factory=list)
    trace: RagTrace = Field(default_factory=RagTrace)


class RagAnswerResult(BaseModel):
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    hits: list[RagHit] = Field(default_factory=list)
    retrieval_trace: RagTrace = Field(default_factory=RagTrace)


class RagHealth(BaseModel):
    enabled: bool = True
    spine: str = "rag-pro"
    vector_backend: str = "memory"
    vector_runtime: str = "memory_dev"
    milvus_uri: str | None = None
    require_real_vector: bool = True
    degraded: bool = False
    document_count: int = 0
    chunk_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class RagStats(BaseModel):
    kb_count: int = 0
    document_count: int = 0
    chunk_count: int = 0
    indexed_chunk_count: int = 0
    vector_backend: str = "memory"
    vector_runtime: str = "memory_dev"
    milvus_uri: str | None = None
    require_real_vector: bool = True

