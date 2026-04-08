from functools import lru_cache

from app.retrieval.private_retriever import PrivateSampleRetriever, get_private_sample_retriever
from app.retrieval.public_retriever import PublicPolicyRetriever, get_public_policy_retriever
from app.retrieval.schemas import RetrievedChunk, RetrievalResult


def _balanced_quota(top_k: int) -> tuple[int, int]:
    public_quota = (top_k + 1) // 2
    private_quota = top_k // 2
    return public_quota, private_quota


class MixedScopeRetriever:
    def __init__(
        self,
        *,
        public_retriever: PublicPolicyRetriever | None = None,
        private_retriever: PrivateSampleRetriever | None = None,
    ) -> None:
        self.public_retriever = public_retriever or get_public_policy_retriever()
        self.private_retriever = private_retriever or get_private_sample_retriever()

    def search(
        self,
        *,
        question: str,
        top_k: int = 5,
        allowed_doc_ids: set[str] | None = None,
    ) -> RetrievalResult:
        public_quota, private_quota = _balanced_quota(top_k)
        public_hits = self.public_retriever.search(
            question=question,
            top_k=top_k,
            knowledge_scope="public",
        ).hits
        private_hits = self.private_retriever.search(
            question=question,
            top_k=top_k,
            knowledge_scope="private_sample",
            allowed_doc_ids=allowed_doc_ids,
        ).hits

        selected_public = public_hits[:public_quota]
        selected_private = private_hits[:private_quota]

        remaining = top_k - len(selected_public) - len(selected_private)
        if remaining > 0:
            public_remaining = public_hits[len(selected_public):]
            private_remaining = private_hits[len(selected_private):]
            refill_pool = [*public_remaining, *private_remaining]
            refill_pool.sort(key=lambda item: item.score, reverse=True)
            refill_hits = refill_pool[:remaining]
        else:
            refill_hits = []

        hits: list[RetrievedChunk] = [*selected_public, *selected_private, *refill_hits]
        hits.sort(key=lambda item: item.score, reverse=True)
        selected_hits = hits[:top_k]
        return RetrievalResult(
            query=question,
            top_k=top_k,
            total_hits=len(selected_hits),
            hits=selected_hits,
        )


@lru_cache(maxsize=1)
def get_mixed_scope_retriever() -> MixedScopeRetriever:
    return MixedScopeRetriever()
