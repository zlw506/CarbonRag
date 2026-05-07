from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from app.rag.contracts import ChunkRecord


class GraphEntity(BaseModel):
    entity_id: str
    name: str
    entity_type: str = "unknown"
    source_chunk_ids: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class GraphRelation(BaseModel):
    relation_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str = "related_to"
    source_chunk_ids: list[str] = Field(default_factory=list)
    weight: float = 1.0
    metadata: dict = Field(default_factory=dict)


class GraphCommunitySummary(BaseModel):
    community_id: str
    title: str
    summary: str
    entity_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class GraphCandidate(BaseModel):
    candidate_id: str
    title: str
    snippet: str
    source_chunk_ids: list[str] = Field(default_factory=list)
    score: float = 0.0
    metadata: dict = Field(default_factory=dict)


class GraphIndexBuildResult(BaseModel):
    status: str
    entity_count: int = 0
    relation_count: int = 0
    community_count: int = 0
    metadata: dict = Field(default_factory=dict)


class GraphIndexBuilder(Protocol):
    def is_available(self) -> bool:
        ...

    def build(self, *, chunks: list[ChunkRecord]) -> GraphIndexBuildResult:
        ...

    def search_candidates(self, *, question: str, top_k: int) -> list[GraphCandidate]:
        ...


class DisabledGraphIndexBuilder:
    def __init__(self, *, reason: str = "graph_index_unavailable") -> None:
        self.reason = reason

    def is_available(self) -> bool:
        return False

    def build(self, *, chunks: list[ChunkRecord]) -> GraphIndexBuildResult:
        return GraphIndexBuildResult(
            status="disabled",
            metadata={"reason": self.reason, "chunk_count": len(chunks)},
        )

    def search_candidates(self, *, question: str, top_k: int) -> list[GraphCandidate]:
        del question, top_k
        return []
