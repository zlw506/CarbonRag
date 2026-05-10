from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


LangChainRagScope = Literal["public", "private_sample", "mixed"]


class LangChainRagDocument(BaseModel):
    page_content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LangChainRagHit(BaseModel):
    chunk_id: str
    knowledge_item_id: str | None = None
    doc_id: str
    title: str
    snippet: str
    source_type: str
    source: str
    source_url: str | None = None
    library_scope: str | None = None
    file_id: str | None = None
    page_number: int | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
    section_title: str | None = None
    score: float = 0.0
    bm25_score: float | None = None
    vector_score: float | None = None
    rerank_score: float | None = None
    source_retrievers: list[str] = Field(default_factory=list)

    def to_tool_hit(self) -> dict[str, Any]:
        return self.model_dump()


class LangChainRagTrace(BaseModel):
    bm25_count: int = 0
    vector_count: int = 0
    merged_count: int = 0
    rerank_applied: bool = False
    hyde_enabled: bool = False
    hyde_applied: bool = False
    hyde_query: str | None = None
    vector_status: str = "disabled"
    vector_backend: str = "chroma"
    fallback_used: bool = False
    fallback_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)


class LangChainRagSearchResult(BaseModel):
    query: str
    hyde_query: str | None = None
    hits: list[LangChainRagHit] = Field(default_factory=list)
    trace: LangChainRagTrace = Field(default_factory=LangChainRagTrace)


class LangChainRagAnswerResult(BaseModel):
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_trace: LangChainRagTrace = Field(default_factory=LangChainRagTrace)
    hits: list[LangChainRagHit] = Field(default_factory=list)


class LangChainRagHealth(BaseModel):
    enabled: bool
    vector_enabled: bool
    bm25_enabled: bool
    hyde_enabled: bool
    rerank_enabled: bool
    vector_backend: str
    vector_available: bool
    vector_reason: str | None = None
    document_count: int = 0
    warning: str | None = None


class LangChainRagIndexStats(BaseModel):
    document_count: int = 0
    public_count: int = 0
    private_count: int = 0
    vector_backend: str = "chroma"
    vector_available: bool = False
    vector_count: int | None = None
    collection: str | None = None
