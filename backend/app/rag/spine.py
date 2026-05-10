from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.rag.kb.models import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    RagAnswerResult,
    RagDocument,
    RagDocumentCreate,
    RagHealth,
    RagHit,
    RagSearchRequest,
    RagSearchResult,
    RagStats,
    RagTrace,
)
from app.rag.kb.storage import RagKnowledgeStore
from app.rag.qa.answer import build_grounded_answer
from app.rag.retrieval.dense import dense_search
from app.rag.retrieval.hybrid_rrf import merge_with_rrf
from app.rag.retrieval.rerank import BgeReranker
from app.rag.retrieval.sparse import sparse_search
from app.rag.vector_backend.base import VectorSearchResult


class RagSpineService:
    """RAG-Pro style primary RAG spine for CarbonRag V1.6.x."""

    def __init__(self, *, store: RagKnowledgeStore | None = None) -> None:
        self.store = store or RagKnowledgeStore()
        self.reranker = BgeReranker()

    def list_kbs(self, *, owner_user_id: str) -> list[KnowledgeBase]:
        return self.store.list_kbs(owner_user_id=owner_user_id)

    def create_kb(self, *, owner_user_id: str, payload: KnowledgeBaseCreate) -> KnowledgeBase:
        return self.store.create_kb(owner_user_id=owner_user_id, payload=payload)

    def get_kb(self, *, owner_user_id: str, kb_id: str) -> KnowledgeBase:
        return self.store.require_kb(owner_user_id=owner_user_id, kb_id=kb_id)

    def update_kb(self, *, owner_user_id: str, kb_id: str, payload: KnowledgeBaseUpdate) -> KnowledgeBase:
        return self.store.update_kb(owner_user_id=owner_user_id, kb_id=kb_id, payload=payload)

    def delete_kb(self, *, owner_user_id: str, kb_id: str) -> None:
        self.store.delete_kb(owner_user_id=owner_user_id, kb_id=kb_id)

    def create_document(self, *, owner_user_id: str, kb_id: str, payload: RagDocumentCreate) -> RagDocument:
        return self.store.create_document(owner_user_id=owner_user_id, kb_id=kb_id, payload=payload.model_dump())

    def list_documents(self, *, owner_user_id: str, kb_id: str) -> list[RagDocument]:
        return self.store.list_documents(owner_user_id=owner_user_id, kb_id=kb_id)

    def get_document(self, *, owner_user_id: str, kb_id: str, doc_id: str) -> RagDocument:
        doc = self.store.get_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)
        if doc is None:
            raise KeyError(doc_id)
        return doc

    def parse_document(self, *, owner_user_id: str, kb_id: str, doc_id: str) -> RagDocument:
        return self.store.parse_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)

    def chunk_document(self, *, owner_user_id: str, kb_id: str, doc_id: str) -> RagDocument:
        return self.store.chunk_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)

    def index_document(self, *, owner_user_id: str, kb_id: str, doc_id: str) -> RagDocument:
        return self.store.index_document(
            owner_user_id=owner_user_id,
            kb_id=kb_id,
            doc_id=doc_id,
            vector_backend=self._effective_vector_backend(),
        )

    def list_chunks(self, *, owner_user_id: str, kb_id: str, doc_id: str | None = None):
        return self.store.list_chunks(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)

    def search(self, *, owner_user_id: str, request: RagSearchRequest) -> RagSearchResult:
        kb_id = request.kb_id
        vector_backend = self._effective_vector_backend()
        if kb_id is None:
            kb = self.store.sync_visible_knowledge(
                owner_user_id=owner_user_id,
                knowledge_scope=request.knowledge_scope,
                allowed_knowledge_item_ids=request.allowed_knowledge_item_ids,
                vector_backend=vector_backend,
            )
            kb_id = kb.kb_id
        chunks = self.store.list_searchable_chunks(
            owner_user_id=owner_user_id,
            kb_id=kb_id,
            knowledge_scope=request.knowledge_scope,
            allowed_knowledge_item_ids=request.allowed_knowledge_item_ids,
        )
        dense_result = (
            VectorSearchResult(hits=[], backend=vector_backend, available=True)
            if request.mode == "sparse"
            else dense_search(query=request.query, chunks=chunks, top_k=max(request.top_k * 4, request.top_k), backend=vector_backend)
        )
        sparse_hits = [] if request.mode == "dense" else sparse_search(query=request.query, chunks=chunks, top_k=max(request.top_k * 4, request.top_k))
        merged = merge_with_rrf(sparse_hits=sparse_hits, dense_hits=dense_result.hits)

        rerank_applied = False
        warning = None
        hits: list[RagHit]
        if request.mode == "hybrid_rerank":
            hits, rerank_applied, warning = self.reranker.rerank(query=request.query, hits=merged, top_k=request.top_k)
        else:
            hits = merged[: request.top_k]

        warnings: list[str] = []
        degraded = False
        if dense_result.warning:
            warnings.append(f"向量后端不可用：{dense_result.warning}")
            degraded = True
        if warning:
            warnings.append(f"重排序未应用：{warning}")
            if request.mode == "hybrid_rerank":
                degraded = True

        trace = RagTrace(
            dense_count=len(dense_result.hits),
            sparse_count=len(sparse_hits),
            merged_count=len(merged),
            rerank_applied=rerank_applied,
            vector_backend=dense_result.backend,
            degraded=degraded,
            warnings=warnings,
            retrieval_mode=request.mode,
            kb_id=kb_id,
            knowledge_scope=request.knowledge_scope,
        )
        return RagSearchResult(query=request.query, kb_id=kb_id, hits=hits, trace=trace)

    def answer(self, *, owner_user_id: str, request: RagSearchRequest) -> RagAnswerResult:
        result = self.search(owner_user_id=owner_user_id, request=request)
        return build_grounded_answer(query=request.query, hits=result.hits, trace=result.trace)

    def test_qa(self, *, owner_user_id: str, request: RagSearchRequest) -> dict:
        result = self.answer(owner_user_id=owner_user_id, request=request)
        kb_id = request.kb_id or result.retrieval_trace.kb_id
        run_id = None
        if kb_id:
            run_id = self.store.record_test_qa(
                owner_user_id=owner_user_id,
                kb_id=kb_id,
                query=request.query,
                answer=result.answer,
                trace=result.retrieval_trace.model_dump(),
                citations=result.citations,
            )
        return {"run_id": run_id, **result.model_dump()}

    def health(self, *, owner_user_id: str | None = None) -> RagHealth:
        stats = self.store.stats(owner_user_id=owner_user_id)
        backend = self._effective_vector_backend()
        warnings = []
        degraded = backend in {"chroma", "memory"}
        if backend == "memory":
            warnings.append("当前使用 memory lexical fallback；比赛验收应使用 milvus_lite + BGE-M3。")
        elif backend == "chroma":
            warnings.append("Chroma 仅保留兼容；V1.6.4 默认验收路径为 milvus_lite。")
        return RagHealth(
            vector_backend=backend,
            degraded=degraded,
            document_count=stats["document_count"],
            chunk_count=stats["chunk_count"],
            warnings=warnings,
        )

    def stats(self, *, owner_user_id: str | None = None) -> RagStats:
        raw = self.store.stats(owner_user_id=owner_user_id)
        return RagStats(**raw, vector_backend=self._effective_vector_backend())

    @staticmethod
    def _effective_vector_backend() -> str:
        backend = str(getattr(get_settings(), "rag_vector_backend", "memory") or "memory").strip().lower()
        if backend in {"milvus", "milvus_lite", "milvus-lite"}:
            return "milvus_lite"
        if backend == "chroma":
            return "chroma"
        return "memory"


@lru_cache(maxsize=1)
def get_rag_spine_service() -> RagSpineService:
    return RagSpineService()

