from functools import lru_cache

import jieba

from app.retrieval.bm25_compat import BM25Okapi
from app.retrieval.public_chunker import chunk_public_policy_document
from app.retrieval.public_corpus_loader import load_public_policy_documents
from app.retrieval.schemas import RetrievedChunk, RetrievalResult


def _tokenize(text: str) -> list[str]:
    return [
        token.strip()
        for token in jieba.lcut_for_search(text)
        if token.strip() and any(character.isalnum() or "\u4e00" <= character <= "\u9fff" for character in token)
    ]


class PublicPolicyRetriever:
    def __init__(self) -> None:
        self.documents = load_public_policy_documents()
        self.chunks: list[RetrievedChunk] = []
        for document in self.documents:
            self.chunks.extend(chunk_public_policy_document(document))
        self._corpus_tokens = [_tokenize(chunk.snippet) for chunk in self.chunks]
        self._bm25 = BM25Okapi(self._corpus_tokens)

    def search(
        self,
        *,
        question: str,
        top_k: int = 5,
        knowledge_scope: str = "public",
        region: str | None = None,
        doc_type: str | None = None,
    ) -> RetrievalResult:
        if knowledge_scope != "public":
            raise ValueError("PublicPolicyRetriever only supports public knowledge scope.")

        query_tokens = _tokenize(question)
        if not query_tokens:
            return RetrievalResult(query=question, top_k=top_k, total_hits=0, hits=[])

        scores = self._bm25.get_scores(query_tokens)
        ranked_hits: list[RetrievedChunk] = []

        for chunk, score in zip(self.chunks, scores, strict=True):
            if region and chunk.region != region:
                continue
            if doc_type and chunk.doc_type != doc_type:
                continue

            title_boost = 0.0
            if any(token in chunk.title for token in query_tokens):
                title_boost = 0.5
            final_score = float(score) + title_boost
            if final_score <= 0:
                continue

            ranked_hits.append(chunk.model_copy(update={"score": round(final_score, 6)}))

        ranked_hits.sort(key=lambda item: item.score, reverse=True)
        selected_hits = ranked_hits[:top_k]
        return RetrievalResult(
            query=question,
            top_k=top_k,
            total_hits=len(selected_hits),
            hits=selected_hits,
        )


@lru_cache(maxsize=1)
def get_public_policy_retriever() -> PublicPolicyRetriever:
    return PublicPolicyRetriever()
