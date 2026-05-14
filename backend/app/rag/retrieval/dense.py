from __future__ import annotations

from app.core.config import get_settings
from app.rag.kb.models import RagChunk
from app.rag.vector_backend import ChromaVectorStoreAdapter, MemoryVectorStore, MilvusVectorStoreAdapter
from app.rag.vector_backend.base import BaseVectorStore, VectorSearchResult

_VECTOR_STORE_CACHE: dict[tuple[str, str], BaseVectorStore] = {}


def get_vector_store(backend: str) -> BaseVectorStore:
    normalized = _normalize_backend(backend)
    cache_key = _vector_store_cache_key(normalized)
    cached = _VECTOR_STORE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    if normalized == "milvus":
        store: BaseVectorStore = MilvusVectorStoreAdapter()
    elif normalized == "chroma":
        store = ChromaVectorStoreAdapter()
    else:
        store = MemoryVectorStore()
    _VECTOR_STORE_CACHE[cache_key] = store
    return store


def reset_vector_store_cache() -> None:
    _VECTOR_STORE_CACHE.clear()


def _normalize_backend(backend: str) -> str:
    normalized = (backend or "memory").strip().lower()
    if normalized in {"milvus", "milvus_standalone", "milvus_lite", "milvus-lite"}:
        return "milvus"
    if normalized == "chroma":
        return "chroma"
    return "memory"


def _vector_store_cache_key(normalized_backend: str) -> tuple[str, str]:
    settings = get_settings()
    if normalized_backend == "milvus":
        return normalized_backend, str(getattr(settings, "rag_milvus_uri", "") or "")
    if normalized_backend == "chroma":
        return normalized_backend, str(getattr(settings, "rag_chroma_persist_dir", "") or "")
    return normalized_backend, ""


def dense_search(*, query: str, chunks: list[RagChunk], top_k: int, backend: str) -> VectorSearchResult:
    return get_vector_store(backend).search(query=query, chunks=chunks, top_k=top_k)
