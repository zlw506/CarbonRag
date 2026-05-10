from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.rag.kb.models import RagChunk


@dataclass(slots=True)
class VectorSearchHit:
    chunk: RagChunk
    score: float


@dataclass(slots=True)
class VectorSearchResult:
    hits: list[VectorSearchHit]
    backend: str
    available: bool
    degraded: bool = False
    warning: str | None = None


@dataclass(slots=True)
class VectorIndexResult:
    indexed_count: int
    backend: str
    available: bool
    degraded: bool = False
    warning: str | None = None


class BaseVectorStore(ABC):
    backend_name: str

    def index_chunks(self, *, chunks: list[RagChunk], embeddings=None) -> VectorIndexResult:
        return VectorIndexResult(
            indexed_count=len(chunks),
            backend=self.backend_name,
            available=True,
        )

    @abstractmethod
    def search(self, *, query: str, chunks: list[RagChunk], top_k: int) -> VectorSearchResult:
        raise NotImplementedError

