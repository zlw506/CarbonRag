from functools import lru_cache

import jieba
from rank_bm25 import BM25Okapi

from app.retrieval.private_chunker import chunk_private_sample_document
from app.retrieval.private_corpus_loader import load_private_sample_documents
from app.retrieval.schemas import RetrievedChunk, RetrievalResult


def _tokenize(text: str) -> list[str]:
    return [
        token.strip()
        for token in jieba.lcut_for_search(text)
        if token.strip() and any(character.isalnum() or "\u4e00" <= character <= "\u9fff" for character in token)
    ]


class PrivateSampleRetriever:
    def __init__(self) -> None:
        self.documents = load_private_sample_documents()
        self.chunks: list[RetrievedChunk] = []
        for document in self.documents:
            self.chunks.extend(chunk_private_sample_document(document))
        self._corpus_tokens = [_tokenize(chunk.snippet) for chunk in self.chunks]
        self._bm25 = BM25Okapi(self._corpus_tokens)

    def search(
        self,
        *,
        question: str,
        top_k: int = 5,
        knowledge_scope: str = "private_sample",
        allowed_doc_ids: set[str] | None = None,
        business_topic: str | None = None,
    ) -> RetrievalResult:
        if knowledge_scope != "private_sample":
            raise ValueError("PrivateSampleRetriever only supports private_sample knowledge scope.")

        query_tokens = _tokenize(question)
        if not query_tokens:
            return RetrievalResult(query=question, top_k=top_k, total_hits=0, hits=[])

        scores = self._bm25.get_scores(query_tokens)
        ranked_hits: list[RetrievedChunk] = []
        for chunk, score in zip(self.chunks, scores, strict=True):
            if allowed_doc_ids is not None and chunk.doc_id not in allowed_doc_ids:
                continue
            if business_topic and chunk.business_topic != business_topic:
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
def get_private_sample_retriever() -> PrivateSampleRetriever:
    return PrivateSampleRetriever()
