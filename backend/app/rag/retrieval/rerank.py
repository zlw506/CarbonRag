from __future__ import annotations

from app.rag.kb.models import RagHit


class LightweightReranker:
    """RAG-Pro style rerank hook; deterministic until BGE reranker is configured."""

    def rerank(self, *, query: str, hits: list[RagHit], top_k: int) -> tuple[list[RagHit], bool, str | None]:
        terms = [term for term in query.lower().split() if term]
        if not hits:
            return [], False, "no_hits"
        reranked: list[RagHit] = []
        for hit in hits:
            text = hit.snippet.lower()
            bonus = sum(1 for term in terms if term in text) / max(len(terms), 1)
            base = hit.rrf_score or hit.dense_score or hit.sparse_score or 0.0
            reranked.append(hit.model_copy(update={"rerank_score": float(base + bonus)}))
        reranked.sort(key=lambda item: item.rerank_score or 0.0, reverse=True)
        return reranked[:top_k], True, None

