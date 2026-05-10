from __future__ import annotations

from app.rag.kb.models import RagChunk
from app.rag.vector_backend.base import BaseVectorStore, VectorIndexResult, VectorSearchResult


class ChromaVectorStoreAdapter(BaseVectorStore):
    backend_name = "chroma"

    def index_chunks(self, *, chunks: list[RagChunk], embeddings=None) -> VectorIndexResult:
        return VectorIndexResult(
            indexed_count=0,
            backend=self.backend_name,
            available=False,
            degraded=True,
            warning="Chroma adapter is compatibility-only in V1.6.4; use milvus_lite for real vector indexing.",
        )

    def search(self, *, query: str, chunks: list[RagChunk], top_k: int) -> VectorSearchResult:
        return VectorSearchResult(
            hits=[],
            backend=self.backend_name,
            available=False,
            degraded=True,
            warning="Chroma adapter is present but not connected to a verified V1.6.3 index in this process.",
        )

