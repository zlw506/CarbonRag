from functools import lru_cache

import jieba

from app.knowledge import get_knowledge_service
from app.retrieval.bm25_compat import BM25Okapi
from app.retrieval.schemas import RetrievedChunk, RetrievalResult


def _tokenize(text: str) -> list[str]:
    return [
        token.strip()
        for token in jieba.lcut_for_search(text)
        if token.strip() and any(character.isalnum() or "\u4e00" <= character <= "\u9fff" for character in token)
    ]


class PrivateSampleRetriever:
    def __init__(self) -> None:
        self.knowledge_service = get_knowledge_service()
        self._refresh_corpus()

    def _refresh_corpus(self) -> None:
        self.knowledge_service.sync_shared_private_samples()
        try:
            self.knowledge_service.run_queued_tasks()
        except Exception:
            pass
        knowledge_items = self.knowledge_service.list_visible_items(owner_user_id=None)
        self.chunks: list[RetrievedChunk] = []
        for item in knowledge_items:
            if not item.is_enabled or item.index_status != "indexed":
                continue
            if item.library_scope not in {"personal", "shared"}:
                continue
            if item.source_type not in {"uploaded_file", "private_sample_repo"}:
                continue
            for chunk in self.knowledge_service.list_chunks(knowledge_item_id=item.knowledge_item_id):
                self.chunks.append(
                    RetrievedChunk(
                        doc_id=item.knowledge_item_id,
                        knowledge_item_id=item.knowledge_item_id,
                        title=chunk.title,
                        source_type="private_upload" if item.source_type == "uploaded_file" else "private_sample",
                        source=chunk.source,
                        source_url=chunk.source_url,
                        issued_at=chunk.issued_at,
                        region=chunk.region,
                        doc_type=chunk.doc_type,
                        sample_type=chunk.sample_type,
                        business_topic=chunk.business_topic,
                        library_scope=item.library_scope,
                        chunk_id=chunk.chunk_id,
                        snippet=chunk.snippet,
                        score=0.0,
                    )
                )
        self._corpus_tokens = [_tokenize(chunk.snippet) for chunk in self.chunks]
        self._bm25 = BM25Okapi(self._corpus_tokens) if self._corpus_tokens else None

    def search(
        self,
        *,
        question: str,
        top_k: int = 5,
        knowledge_scope: str = "private_sample",
        allowed_knowledge_item_ids: set[str] | None = None,
        allowed_doc_ids: set[str] | None = None,
        business_topic: str | None = None,
    ) -> RetrievalResult:
        if knowledge_scope != "private_sample":
            raise ValueError("PrivateSampleRetriever only supports private_sample knowledge scope.")

        if allowed_knowledge_item_ids is not None:
            allowed_ids = allowed_knowledge_item_ids
        elif allowed_doc_ids is not None:
            allowed_ids = allowed_doc_ids
        else:
            allowed_ids = None
        query_tokens = _tokenize(question)
        if not query_tokens or self._bm25 is None:
            return RetrievalResult(query=question, top_k=top_k, total_hits=0, hits=[])

        scores = self._bm25.get_scores(query_tokens)
        ranked_hits: list[RetrievedChunk] = []
        for chunk, score in zip(self.chunks, scores, strict=True):
            if allowed_ids is not None and chunk.knowledge_item_id not in allowed_ids:
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
