from __future__ import annotations

from app.rag.kb.models import RagChunk
from app.rag.vector_backend.base import BaseVectorStore, VectorSearchResult


class MilvusVectorStoreAdapter(BaseVectorStore):
    backend_name = "milvus_lite"

    def search(self, *, query: str, chunks: list[RagChunk], top_k: int) -> VectorSearchResult:
        return VectorSearchResult(
            hits=[],
            backend=self.backend_name,
            available=False,
            degraded=True,
            warning="Milvus Lite/Milvus adapter is defined, but pymilvus/BGE-M3 runtime is not configured in this environment.",
        )

