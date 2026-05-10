from __future__ import annotations

from app.rag.kb.models import RagChunk
from app.rag.vector_backend import ChromaVectorStoreAdapter, MemoryVectorStore, MilvusVectorStoreAdapter
from app.rag.vector_backend.base import BaseVectorStore, VectorSearchResult


def get_vector_store(backend: str) -> BaseVectorStore:
    normalized = (backend or "memory").strip().lower()
    if normalized in {"milvus", "milvus_standalone", "milvus_lite", "milvus-lite"}:
        return MilvusVectorStoreAdapter()
    if normalized == "chroma":
        return ChromaVectorStoreAdapter()
    return MemoryVectorStore()


def dense_search(*, query: str, chunks: list[RagChunk], top_k: int, backend: str) -> VectorSearchResult:
    return get_vector_store(backend).search(query=query, chunks=chunks, top_k=top_k)
