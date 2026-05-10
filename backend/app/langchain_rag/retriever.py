from __future__ import annotations

from app.langchain_rag.bm25_store import LangChainBm25Store
from app.langchain_rag.config import LangChainRagConfig
from app.langchain_rag.reranker import CrossEncoderReranker
from app.langchain_rag.schemas import LangChainRagDocument, LangChainRagHit, LangChainRagTrace
from app.langchain_rag.vector_store import ChromaVectorStore


class HybridLangChainRetriever:
    def __init__(
        self,
        *,
        config: LangChainRagConfig,
        vector_store: ChromaVectorStore,
        reranker: CrossEncoderReranker,
    ) -> None:
        self.config = config
        self.vector_store = vector_store
        self.reranker = reranker

    def retrieve(
        self,
        *,
        query: str,
        retrieval_query: str,
        documents: list[LangChainRagDocument],
        top_k: int,
        trace: LangChainRagTrace,
    ) -> tuple[list[LangChainRagHit], LangChainRagTrace]:
        bm25_hits = []
        if self.config.bm25_enabled:
            bm25_hits = LangChainBm25Store(documents).search(query=retrieval_query, top_k=max(top_k * 2, top_k))
        vector_hits = self.vector_store.search(
            query=retrieval_query,
            top_k=max(top_k * 2, top_k),
            candidate_documents=documents,
        )
        weights = _dynamic_weights(query)
        merged = _merge_hits(bm25_hits=bm25_hits, vector_hits=vector_hits, weights=weights)
        reranked, rerank_applied = self.reranker.rerank(query=query, hits=merged, top_k=top_k)

        vector_health = self.vector_store.health()
        trace.bm25_count = len(bm25_hits)
        trace.vector_count = len(vector_hits)
        trace.merged_count = len(merged)
        trace.rerank_applied = rerank_applied
        trace.vector_status = "queried" if vector_hits else "unavailable" if not vector_health["available"] else "empty"
        trace.vector_backend = "chroma"
        trace.weights = weights
        if not vector_health["available"]:
            trace.fallback_used = True
            trace.fallback_reason = vector_health.get("reason") or "vector_unavailable"
            trace.warnings.append(f"向量检索不可用：{trace.fallback_reason}")
        if self.config.rerank_enabled and not rerank_applied:
            reason = self.reranker.reason or "rerank_unavailable"
            trace.warnings.append(f"重排序未应用：{reason}")
        return reranked, trace


def _dynamic_weights(query: str) -> dict[str, float]:
    length = len(query.strip())
    token_count = len(query.split())
    if length <= 20 or token_count <= 8:
        return {"bm25": 0.7, "vector": 0.3}
    if length >= 80 or token_count >= 40:
        return {"bm25": 0.3, "vector": 0.7}
    return {"bm25": 0.5, "vector": 0.5}


def _merge_hits(
    *,
    bm25_hits: list[LangChainRagHit],
    vector_hits: list[LangChainRagHit],
    weights: dict[str, float],
) -> list[LangChainRagHit]:
    records: dict[str, dict] = {}
    bm25_max = max((hit.bm25_score or hit.score for hit in bm25_hits), default=0.0) or 1.0
    vector_max = max((hit.vector_score or hit.score for hit in vector_hits), default=0.0) or 1.0

    for hit in bm25_hits:
        score = (hit.bm25_score or hit.score) / bm25_max
        records[hit.chunk_id] = {"hit": hit, "bm25": score, "vector": 0.0, "source_retrievers": ["bm25"]}

    for hit in vector_hits:
        score = (hit.vector_score or hit.score) / vector_max
        record = records.setdefault(hit.chunk_id, {"hit": hit, "bm25": 0.0, "vector": 0.0, "source_retrievers": []})
        record["vector"] = score
        if "vector" not in record["source_retrievers"]:
            record["source_retrievers"].append("vector")

    merged: list[LangChainRagHit] = []
    for record in records.values():
        score = float(record["bm25"]) * weights["bm25"] + float(record["vector"]) * weights["vector"]
        hit: LangChainRagHit = record["hit"]
        merged.append(hit.model_copy(update={"score": score, "source_retrievers": list(record["source_retrievers"])}))
    merged.sort(key=lambda hit: hit.score, reverse=True)
    return merged
