from __future__ import annotations

from app.rag.kb.models import RagChunk
from app.rag.vector_backend.base import BaseVectorStore, VectorSearchResult


class ChromaVectorStoreAdapter(BaseVectorStore):
    backend_name = "chroma"

    def search(self, *, query: str, chunks: list[RagChunk], top_k: int) -> VectorSearchResult:
        return VectorSearchResult(
            hits=[],
            backend=self.backend_name,
            available=False,
            degraded=True,
            warning="Chroma adapter is present but not connected to a verified V1.6.3 index in this process.",
        )

