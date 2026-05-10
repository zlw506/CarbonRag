from __future__ import annotations

from pathlib import Path
from typing import Any

from app.langchain_rag.config import LangChainRagConfig
from app.langchain_rag.documents import to_langchain_documents
from app.langchain_rag.embeddings import CarbonRagEmbeddings
from app.langchain_rag.schemas import LangChainRagDocument, LangChainRagHit
from app.langchain_rag.bm25_store import _hit_from_document

try:  # pragma: no cover - exercised when langchain-chroma is installed
    from langchain_chroma import Chroma
except Exception:  # noqa: BLE001
    Chroma = None  # type: ignore[assignment]


class ChromaVectorStore:
    def __init__(self, *, config: LangChainRagConfig) -> None:
        self.config = config
        self._store = None
        self._reason: str | None = None

    def health(self) -> dict[str, Any]:
        store = self._get_store()
        return {
            "backend": "chroma",
            "available": store is not None,
            "reason": self._reason,
            "collection": self.config.chroma_collection,
            "persist_dir": self.config.chroma_persist_dir,
        }

    def rebuild(self, documents: list[LangChainRagDocument]) -> dict[str, Any]:
        store = self._get_store(force=True)
        if store is None:
            return {"backend": "chroma", "available": False, "upserted_count": 0, "reason": self._reason}
        try:
            if hasattr(store, "delete_collection"):
                store.delete_collection()
                self._store = None
                store = self._get_store(force=True)
            ids = [_document_id(document) for document in documents]
            langchain_docs = to_langchain_documents(documents)
            if langchain_docs:
                store.add_documents(langchain_docs, ids=ids)
            return {"backend": "chroma", "available": True, "upserted_count": len(documents), "reason": None}
        except Exception as exc:  # noqa: BLE001
            self._reason = f"{type(exc).__name__}: {exc}"
            return {"backend": "chroma", "available": False, "upserted_count": 0, "reason": self._reason}

    def upsert(self, documents: list[LangChainRagDocument]) -> dict[str, Any]:
        store = self._get_store()
        if store is None:
            return {"backend": "chroma", "available": False, "upserted_count": 0, "reason": self._reason}
        try:
            ids = [_document_id(document) for document in documents]
            try:
                store.delete(ids=ids)
            except Exception:  # noqa: BLE001
                pass
            store.add_documents(to_langchain_documents(documents), ids=ids)
            return {"backend": "chroma", "available": True, "upserted_count": len(documents), "reason": None}
        except Exception as exc:  # noqa: BLE001
            self._reason = f"{type(exc).__name__}: {exc}"
            return {"backend": "chroma", "available": False, "upserted_count": 0, "reason": self._reason}

    def search(self, *, query: str, top_k: int, candidate_documents: list[LangChainRagDocument]) -> list[LangChainRagHit]:
        store = self._get_store()
        if store is None:
            return []
        try:
            raw_results = store.similarity_search_with_relevance_scores(query, k=max(top_k * 6, top_k))
        except Exception as exc:  # noqa: BLE001
            self._reason = f"{type(exc).__name__}: {exc}"
            return []
        allowed_chunk_ids = {document.metadata.get("chunk_id") for document in candidate_documents}
        hits: list[LangChainRagHit] = []
        for document, score in raw_results:
            metadata = dict(getattr(document, "metadata", {}) or {})
            if metadata.get("chunk_id") not in allowed_chunk_ids:
                continue
            hits.append(
                _hit_from_document(
                    LangChainRagDocument(page_content=getattr(document, "page_content", ""), metadata=metadata),
                    vector_score=float(score),
                    source_retrievers=["vector"],
                )
            )
            if len(hits) >= top_k:
                break
        return hits

    def _get_store(self, *, force: bool = False):
        if not self.config.vector_enabled:
            self._reason = "rag_vector_disabled"
            return None
        if Chroma is None:
            self._reason = "langchain_chroma_not_installed"
            return None
        if self._store is not None and not force:
            return self._store
        try:
            Path(self.config.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
            self._store = Chroma(
                collection_name=self.config.chroma_collection,
                embedding_function=CarbonRagEmbeddings(),
                persist_directory=self.config.chroma_persist_dir,
            )
            self._reason = None
            return self._store
        except Exception as exc:  # noqa: BLE001
            self._reason = f"{type(exc).__name__}: {exc}"
            self._store = None
            return None


def _document_id(document: LangChainRagDocument) -> str:
    return str(document.metadata.get("chunk_id") or document.metadata.get("knowledge_item_id") or hash(document.page_content))
