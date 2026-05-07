from dataclasses import dataclass, field
from typing import Protocol

from app.retrieval.schemas import RetrievedChunk


@dataclass(frozen=True)
class VectorSearchResult:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class BaseVectorRetriever(Protocol):
    def is_available(self) -> bool:
        ...

    def requires_embedding(self) -> bool:
        ...

    def search(
        self,
        *,
        question: str,
        query_embedding: list[float] | None,
        top_k: int,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> VectorSearchResult:
        ...


@dataclass
class DisabledVectorRetriever:
    reason: str = "rag_vector_disabled"

    def is_available(self) -> bool:
        return False

    def requires_embedding(self) -> bool:
        return False

    def search(
        self,
        *,
        question: str,
        query_embedding: list[float] | None,
        top_k: int,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> VectorSearchResult:
        return VectorSearchResult(
            chunks=[],
            metadata={
                "status": "disabled",
                "reason": self.reason,
                "query_length": len(question),
                "top_k": top_k,
                "allowed_knowledge_item_count": len(allowed_knowledge_item_ids or set()),
            },
        )
