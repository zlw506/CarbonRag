from __future__ import annotations

import jieba

from app.retrieval.bm25_compat import BM25Okapi
from app.langchain_rag.schemas import LangChainRagDocument, LangChainRagHit


class LangChainBm25Store:
    def __init__(self, documents: list[LangChainRagDocument] | None = None) -> None:
        self.documents = documents or []
        self._tokens = [_tokenize(document.page_content) for document in self.documents]
        self._bm25 = BM25Okapi(self._tokens) if self._tokens else None

    def search(self, *, query: str, top_k: int) -> list[LangChainRagHit]:
        if self._bm25 is None:
            return []
        query_tokens = _tokenize(query)
        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(enumerate(scores), key=lambda item: float(item[1]), reverse=True)
        hits: list[LangChainRagHit] = []
        for index, score in ranked[:top_k]:
            normalized_score = float(score)
            if normalized_score <= 0:
                normalized_score = _overlap_score(self._tokens[index], query_tokens)
            if normalized_score <= 0:
                continue
            hits.append(_hit_from_document(self.documents[index], bm25_score=normalized_score, source_retrievers=["bm25"]))
        return hits


def _tokenize(text: str) -> list[str]:
    return [token.strip() for token in jieba.lcut_for_search(text or "") if token.strip()]


def _overlap_score(document_tokens: list[str], query_tokens: list[str]) -> float:
    if not document_tokens or not query_tokens:
        return 0.0
    overlap = len(set(document_tokens).intersection(query_tokens))
    return float(overlap) / max(len(set(query_tokens)), 1)


def _hit_from_document(
    document: LangChainRagDocument,
    *,
    bm25_score: float | None = None,
    vector_score: float | None = None,
    source_retrievers: list[str],
) -> LangChainRagHit:
    metadata = document.metadata
    return LangChainRagHit(
        chunk_id=str(metadata.get("chunk_id") or ""),
        knowledge_item_id=_optional_str(metadata.get("knowledge_item_id")),
        doc_id=str(metadata.get("doc_id") or metadata.get("knowledge_item_id") or metadata.get("chunk_id") or ""),
        title=str(metadata.get("title") or "未命名知识片段"),
        snippet=document.page_content,
        source_type=str(metadata.get("source_type") or "public_policy"),
        source=str(metadata.get("source") or ""),
        source_url=_optional_str(metadata.get("source_url")),
        library_scope=_optional_str(metadata.get("library_scope")),
        file_id=_optional_str(metadata.get("file_id")),
        page_number=_optional_int(metadata.get("page_number")),
        sheet_name=_optional_str(metadata.get("sheet_name")),
        slide_number=_optional_int(metadata.get("slide_number")),
        section_title=_optional_str(metadata.get("section_title")),
        score=float(bm25_score or vector_score or 0.0),
        bm25_score=bm25_score,
        vector_score=vector_score,
        source_retrievers=source_retrievers,
    )


def _optional_str(value) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _optional_int(value) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
