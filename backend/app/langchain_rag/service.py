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
    LangChainRagIndexStats,
    LangChainRagScope,
    LangChainRagSearchResult,
    LangChainRagTrace,
)
from app.langchain_rag.vector_store import ChromaVectorStore


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
            trace.fallback_used = False
            trace.fallback_reason = None
            trace.warnings.append("LangChain RAG 未命中；按 V1.6.3 规则不再回退旧 RagEngineService。")
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
