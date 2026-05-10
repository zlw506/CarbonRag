from __future__ import annotations

from functools import lru_cache

from app.langchain_rag.answer_chain import LangChainRagAnswerChain
from app.langchain_rag.config import LangChainRagConfig, get_langchain_rag_config
from app.langchain_rag.documents import load_all_indexable_documents, load_file_documents, load_visible_documents
from app.langchain_rag.hyde import HyDEGenerator
from app.langchain_rag.reranker import CrossEncoderReranker
from app.langchain_rag.retriever import HybridLangChainRetriever
from app.langchain_rag.schemas import (
    LangChainRagAnswerResult,
    LangChainRagHealth,
    LangChainRagHit,
    LangChainRagIndexStats,
    LangChainRagScope,
    LangChainRagSearchResult,
    LangChainRagTrace,
)
from app.langchain_rag.vector_store import ChromaVectorStore
from app.rag import build_rag_query_params, get_rag_engine_service


class LangChainRagService:
    def __init__(self, *, config: LangChainRagConfig | None = None) -> None:
        self.config = config or get_langchain_rag_config()
        self.vector_store = ChromaVectorStore(config=self.config)
        self.reranker = CrossEncoderReranker(config=self.config)
        self.retriever = HybridLangChainRetriever(
            config=self.config,
            vector_store=self.vector_store,
            reranker=self.reranker,
        )
        self.hyde = HyDEGenerator()
        self.answer_chain = LangChainRagAnswerChain()

    def health(self, *, owner_user_id: str | None = None) -> LangChainRagHealth:
        documents = load_all_indexable_documents() if owner_user_id is None else load_visible_documents(
            owner_user_id=owner_user_id,
            knowledge_scope="mixed",
            allowed_knowledge_item_ids=[],
        )
        vector_health = self.vector_store.health()
        return LangChainRagHealth(
            enabled=self.config.enabled,
            vector_enabled=self.config.vector_enabled,
            bm25_enabled=self.config.bm25_enabled,
            hyde_enabled=self.config.hyde_enabled,
            rerank_enabled=self.config.rerank_enabled,
            vector_backend="chroma",
            vector_available=bool(vector_health["available"]),
            vector_reason=vector_health.get("reason"),
            document_count=len(documents),
            warning=None if self.config.enabled else "RAG_LANGCHAIN_ENABLED=false",
        )

    def stats(self) -> LangChainRagIndexStats:
        documents = load_all_indexable_documents()
        vector_health = self.vector_store.health()
        public_count = sum(1 for doc in documents if str(doc.metadata.get("source_type", "")).startswith("public_policy"))
        private_count = len(documents) - public_count
        return LangChainRagIndexStats(
            document_count=len(documents),
            public_count=public_count,
            private_count=private_count,
            vector_available=bool(vector_health["available"]),
            collection=self.config.chroma_collection,
        )

    def rebuild_index(self) -> dict:
        documents = load_all_indexable_documents()
        result = self.vector_store.rebuild(documents)
        return {"document_count": len(documents), **result}

    def index_file(self, *, owner_user_id: str, file_id: str) -> dict:
        documents = load_file_documents(owner_user_id=owner_user_id, file_id=file_id)
        result = self.vector_store.upsert(documents)
        return {"file_id": file_id, "document_count": len(documents), **result}

    def search(
        self,
        *,
        owner_user_id: str,
        query: str,
        knowledge_scope: LangChainRagScope,
        top_k: int,
        allowed_knowledge_item_ids: list[str] | None = None,
    ) -> LangChainRagSearchResult:
        trace = LangChainRagTrace(
            hyde_enabled=self.config.hyde_enabled,
            vector_backend="chroma",
        )
        documents = load_visible_documents(
            owner_user_id=owner_user_id,
            knowledge_scope=knowledge_scope,
            allowed_knowledge_item_ids=allowed_knowledge_item_ids,
        )
        retrieval_query = query
        if self.config.hyde_enabled:
            retrieval_query, hyde_warnings = self.hyde.generate(query)
            trace.hyde_query = retrieval_query
            trace.hyde_applied = retrieval_query != query
            trace.warnings.extend(hyde_warnings)
        hits, trace = self.retriever.retrieve(
            query=query,
            retrieval_query=retrieval_query,
            documents=documents,
            top_k=top_k,
            trace=trace,
        )
        if not hits:
            legacy_hits = _legacy_fallback_hits(
                query=query,
                knowledge_scope=knowledge_scope,
                top_k=top_k,
                allowed_knowledge_item_ids=allowed_knowledge_item_ids or [],
            )
            if legacy_hits:
                hits = legacy_hits
                trace.fallback_used = True
                trace.fallback_reason = "legacy_rag_fallback"
                trace.merged_count = len(hits)
                trace.warnings.append("LangChain RAG 未命中，已回退旧 RAG 检索路径。")
        return LangChainRagSearchResult(query=query, hyde_query=trace.hyde_query, hits=hits, trace=trace)

    def answer(
        self,
        *,
        owner_user_id: str,
        query: str,
        knowledge_scope: LangChainRagScope,
        top_k: int,
        allowed_knowledge_item_ids: list[str] | None = None,
    ) -> LangChainRagAnswerResult:
        search_result = self.search(
            owner_user_id=owner_user_id,
            query=query,
            knowledge_scope=knowledge_scope,
            top_k=top_k,
            allowed_knowledge_item_ids=allowed_knowledge_item_ids,
        )
        return self.answer_chain.answer(question=query, hits=search_result.hits, trace=search_result.trace)


@lru_cache(maxsize=1)
def get_langchain_rag_service() -> LangChainRagService:
    return LangChainRagService()


def _legacy_fallback_hits(
    *,
    query: str,
    knowledge_scope: LangChainRagScope,
    top_k: int,
    allowed_knowledge_item_ids: list[str],
) -> list[LangChainRagHit]:
    try:
        result = get_rag_engine_service().retrieve(
            build_rag_query_params(
                question=query,
                knowledge_scope=knowledge_scope,
                top_k=top_k,
                allowed_knowledge_item_ids=allowed_knowledge_item_ids,
            )
        )
    except Exception:  # noqa: BLE001
        return []
    hits: list[LangChainRagHit] = []
    for item in result.hits:
        score = float(item.get("score") or 0.0)
        hits.append(
            LangChainRagHit(
                chunk_id=str(item.get("chunk_id") or ""),
                knowledge_item_id=_optional_str(item.get("knowledge_item_id") or item.get("doc_id")),
                doc_id=str(item.get("doc_id") or item.get("knowledge_item_id") or item.get("chunk_id") or ""),
                title=str(item.get("title") or "旧 RAG 命中片段"),
                snippet=str(item.get("snippet") or ""),
                source_type=str(item.get("source_type") or "public_policy"),
                source=str(item.get("source") or ""),
                source_url=_optional_str(item.get("source_url")),
                library_scope=_optional_str(item.get("library_scope")),
                file_id=_optional_str(item.get("file_id")),
                page_number=_optional_int(item.get("page_number")),
                sheet_name=_optional_str(item.get("sheet_name")),
                slide_number=_optional_int(item.get("slide_number")),
                section_title=_optional_str(item.get("section_title")),
                score=score,
                bm25_score=score,
                source_retrievers=["legacy_rag_fallback"],
            )
        )
    return hits


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
