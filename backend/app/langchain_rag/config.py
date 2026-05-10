from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class LangChainRagConfig:
    enabled: bool
    vector_enabled: bool
    vector_backend: str
    bm25_enabled: bool
    hyde_enabled: bool
    rerank_enabled: bool
    rerank_provider: str
    rerank_model: str
    chroma_persist_dir: str
    chroma_collection: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    langsmith_tracing: bool


def get_langchain_rag_config(settings: Settings | None = None) -> LangChainRagConfig:
    resolved = settings or get_settings()
    return LangChainRagConfig(
        enabled=bool(getattr(resolved, "rag_langchain_enabled", False)),
        vector_enabled=bool(getattr(resolved, "rag_vector_enabled", False)),
        vector_backend=str(getattr(resolved, "rag_vector_backend", "chroma") or "chroma"),
        bm25_enabled=bool(getattr(resolved, "rag_bm25_enabled", True)),
        hyde_enabled=bool(getattr(resolved, "rag_hyde_enabled", True)),
        rerank_enabled=bool(getattr(resolved, "rag_rerank_enabled", True)),
        rerank_provider=str(getattr(resolved, "rag_rerank_provider", "cross_encoder") or "cross_encoder"),
        rerank_model=str(getattr(resolved, "rag_rerank_model", "BAAI/bge-reranker-base") or "BAAI/bge-reranker-base"),
        chroma_persist_dir=str(getattr(resolved, "rag_chroma_persist_dir", "./data/outputs/chroma") or "./data/outputs/chroma"),
        chroma_collection=str(getattr(resolved, "rag_chroma_collection", "carbonrag_langchain") or "carbonrag_langchain"),
        chunk_size=int(getattr(resolved, "rag_langchain_chunk_size", 800) or 800),
        chunk_overlap=int(getattr(resolved, "rag_langchain_chunk_overlap", 120) or 120),
        top_k=int(getattr(resolved, "rag_langchain_default_top_k", 5) or 5),
        langsmith_tracing=bool(getattr(resolved, "rag_langsmith_tracing", False)),
    )
