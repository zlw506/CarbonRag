from functools import lru_cache
from time import perf_counter

from app.ai_runtime.providers.base import BaseEmbeddingProvider, BaseRerankProvider, RerankItem
from app.ai_runtime.providers.factory import get_embedding_provider, get_rerank_provider
from app.core.config import Settings, get_settings
from app.rag.adapters import citation_refs_from_references
from app.rag.contracts import RetrievalTrace
from app.rag.schemas import (
    RagEvidenceChunk,
    RagEvidenceReference,
    RagKnowledgeScope,
    RagQueryParams,
    RagRetrievalMetadata,
    RagRetrievalResult,
)
from app.rag.strategy import build_retrieval_path, plan_retrieval_strategy
from app.rag.vector import BaseVectorRetriever, DisabledVectorRetriever
from app.rag.vector_store import CurrentVectorStoreAdapter, VectorStoreAdapter, VectorStoreHealth
from app.retrieval.mixed_retriever import MixedScopeRetriever, get_mixed_scope_retriever
from app.retrieval.private_retriever import PrivateSampleRetriever, get_private_sample_retriever
from app.retrieval.public_retriever import PublicPolicyRetriever, get_public_policy_retriever
from app.retrieval.schemas import RetrievedChunk, RetrievalResult


class RagEngineService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        vector_retriever: BaseVectorRetriever | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        rerank_provider: BaseRerankProvider | None = None,
        public_retriever: PublicPolicyRetriever | None = None,
        private_retriever: PrivateSampleRetriever | None = None,
        mixed_retriever: MixedScopeRetriever | None = None,
        vector_store_adapter: VectorStoreAdapter | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.vector_retriever = vector_retriever or DisabledVectorRetriever()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.rerank_provider = rerank_provider or get_rerank_provider()
        self.public_retriever = public_retriever or get_public_policy_retriever()
        self.private_retriever = private_retriever or get_private_sample_retriever()
        self.mixed_retriever = mixed_retriever or get_mixed_scope_retriever()
        self.vector_store_adapter = vector_store_adapter or CurrentVectorStoreAdapter(
            public_retriever=self.public_retriever,
            private_retriever=self.private_retriever,
            mixed_retriever=self.mixed_retriever,
        )

    def retrieve(self, params: RagQueryParams) -> RagRetrievalResult:
        started_at = perf_counter()
        chunk_top_k = params.chunk_top_k or params.top_k
        strategy_plan = plan_retrieval_strategy(mode=params.mode, knowledge_scope=params.knowledge_scope)
        provider_metadata: dict = {}
        vector_status = "disabled"
        fallback_reason = self._initial_fallback_reason()
        vector_hits: list[RetrievedChunk] = []
        vector_store_health = self._vector_store_health()
        provider_metadata["vector_store"] = vector_store_health.model_dump()

        if self.settings.rag_engine_enabled and self.settings.rag_vector_enabled:
            if self.vector_retriever.is_available():
                try:
                    query_embedding = self._resolve_query_embedding(params.question)
                    vector_result = self.vector_retriever.search(
                        question=params.question,
                        query_embedding=query_embedding,
                        top_k=chunk_top_k,
                        allowed_knowledge_item_ids=set(params.allowed_knowledge_item_ids) or None,
                    )
                    vector_hits = vector_result.chunks
                    provider_metadata["vector"] = vector_result.metadata
                    vector_status = "queried"
                    fallback_reason = None if vector_hits else "vector_returned_no_hits"
                except Exception as exc:  # noqa: BLE001
                    vector_status = "error"
                    fallback_reason = "vector_retrieval_error"
                    provider_metadata["vector_error"] = {"type": type(exc).__name__, "message": str(exc)}
            else:
                vector_status = "unavailable"
                fallback_reason = "vector_retriever_unavailable"

        if vector_hits:
            selected_hits = vector_hits[:chunk_top_k]
            retrieval_layer = "vector"
        else:
            fallback_result = self._fallback_search(params)
            selected_hits = fallback_result.hits
            retrieval_layer = "bm25_fallback"
            provider_metadata["fallback"] = {
                "total_hits": fallback_result.total_hits,
                "scope": params.knowledge_scope,
            }

        selected_hits, rerank_status = self._maybe_rerank(
            params=params,
            hits=selected_hits,
            provider_metadata=provider_metadata,
        )
        selected_hits = self._apply_metadata_filters(params=params, hits=selected_hits)

        chunks = [
            self._build_evidence_chunk(
                hit=hit,
                index=index,
                retrieval_layer=retrieval_layer,
            )
            for index, hit in enumerate(selected_hits[: params.top_k], start=1)
        ]
        references = [
            RagEvidenceReference(
                reference_id=chunk.reference_id,
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                title=chunk.title,
                source_type=chunk.source_type,
                source=chunk.source,
                source_url=chunk.source_url,
            )
            for chunk in chunks
        ]
        graph_status = "unavailable" if params.mode == "mix" else "skipped"
        retrieval_path = build_retrieval_path(
            retrieval_layer=retrieval_layer,
            vector_status=vector_status,
            graph_status=graph_status,
            rerank_status=rerank_status,
        )
        latency_ms = round((perf_counter() - started_at) * 1000, 3)
        fallback_used = retrieval_layer == "bm25_fallback"
        citation_refs = citation_refs_from_references(references, chunks=chunks)
        trace = RetrievalTrace(
            query=params.question,
            retriever_mode=retrieval_layer,
            requested_top_k=params.top_k,
            returned_count=len(chunks),
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            chunk_ids=[chunk.chunk_id for chunk in chunks],
            citations=citation_refs,
            strategy=strategy_plan.name,
            retrieval_path=retrieval_path,
            latency_ms=latency_ms,
            total_hits=len(chunks),
            metadata={
                "planned_layers": strategy_plan.planned_layers,
                "provider_metadata_keys": sorted(provider_metadata.keys()),
                "vector_backend": vector_store_health.backend,
                "vector_backend_health": vector_store_health.status,
                "vector_adapter_name": self._vector_adapter_name(vector_store_health),
            },
        )
        public_chunk_count, private_chunk_count = self._count_chunk_scopes(chunks)

        metadata = RagRetrievalMetadata(
            mode=params.mode,
            knowledge_scope=params.knowledge_scope,
            top_k=params.top_k,
            chunk_top_k=chunk_top_k,
            retrieval_only=params.retrieval_only,
            retriever_mode=retrieval_layer,
            requested_top_k=params.top_k,
            returned_count=len(chunks),
            fallback_used=fallback_used,
            strategy=strategy_plan.name,
            retrieval_path=retrieval_path,
            vector_status=vector_status,
            vector_backend=vector_store_health.backend,
            vector_backend_health=vector_store_health.status,
            vector_adapter_name=self._vector_adapter_name(vector_store_health),
            graph_status=graph_status,
            rerank_status=rerank_status,
            fallback_reason=fallback_reason,
            latency_ms=trace.latency_ms,
            public_chunk_count=public_chunk_count,
            private_chunk_count=private_chunk_count,
            trace=trace,
            provider_metadata=provider_metadata,
        )
        return RagRetrievalResult(
            query=params.question,
            total_hits=len(chunks),
            chunks=chunks,
            references=references if params.include_references else [],
            metadata=metadata,
        )

    def _initial_fallback_reason(self) -> str | None:
        if not self.settings.rag_engine_enabled:
            return "rag_engine_disabled"
        if not self.settings.rag_vector_enabled:
            return "rag_vector_disabled"
        return None

    def _resolve_query_embedding(self, question: str) -> list[float] | None:
        if not self.vector_retriever.requires_embedding():
            return None
        embedding_result = self.embedding_provider.embed_stub([question])
        if not embedding_result.vectors:
            return None
        return embedding_result.vectors[0]

    def _fallback_search(self, params: RagQueryParams) -> RetrievalResult:
        allowed_ids = set(params.allowed_knowledge_item_ids) or None
        adapter_result = self.vector_store_adapter.search(
            question=params.question,
            top_k=params.top_k,
            filters={
                "knowledge_scope": params.knowledge_scope,
                "region": params.region,
                "doc_type": params.doc_type,
                "allowed_knowledge_item_ids": list(allowed_ids or []),
            },
            allowed_knowledge_item_ids=allowed_ids,
        )
        return RetrievalResult(
            query=params.question,
            top_k=params.top_k,
            total_hits=adapter_result.total_hits,
            hits=adapter_result.chunks,
        )

    def _maybe_rerank(
        self,
        *,
        params: RagQueryParams,
        hits: list[RetrievedChunk],
        provider_metadata: dict,
    ) -> tuple[list[RetrievedChunk], str]:
        if not params.enable_rerank:
            return hits, "disabled"
        if not self.settings.rag_rerank_enabled:
            return hits, "disabled"
        try:
            rerank_items = [
                RerankItem(
                    item_id=hit.chunk_id,
                    text=hit.snippet,
                    metadata={"doc_id": hit.doc_id, "source_type": hit.source_type},
                )
                for hit in hits
            ]
            rerank_result = self.rerank_provider.rerank_stub(
                query=params.question,
                items=rerank_items,
                top_k=params.top_k,
            )
            provider_metadata["rerank"] = rerank_result.metadata
            if rerank_result.metadata.get("status") == "skipped":
                return hits, "skipped"
            order = {chunk_id: index for index, chunk_id in enumerate(rerank_result.ranked_ids)}
            reranked = sorted(
                hits,
                key=lambda hit: order.get(hit.chunk_id, len(order)),
            )
            return reranked[: params.top_k], "applied"
        except Exception as exc:  # noqa: BLE001
            provider_metadata["rerank_error"] = {"type": type(exc).__name__, "message": str(exc)}
            return hits, "error"

    @staticmethod
    def _apply_metadata_filters(
        *,
        params: RagQueryParams,
        hits: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        filtered = hits
        if params.region:
            filtered = [hit for hit in filtered if hit.region == params.region]
        if params.doc_type:
            filtered = [hit for hit in filtered if hit.doc_type == params.doc_type]
        return filtered

    @staticmethod
    def _build_evidence_chunk(
        *,
        hit: RetrievedChunk,
        index: int,
        retrieval_layer: str,
    ) -> RagEvidenceChunk:
        return RagEvidenceChunk(
            reference_id=f"ref-{index}",
            doc_id=hit.doc_id,
            knowledge_item_id=hit.knowledge_item_id,
            title=hit.title,
            source_type=hit.source_type,
            source=hit.source,
            source_url=hit.source_url,
            issued_at=hit.issued_at,
            region=hit.region,
            doc_type=hit.doc_type,
            sample_type=hit.sample_type,
            business_topic=hit.business_topic,
            library_scope=hit.library_scope,
            chunk_id=hit.chunk_id,
            snippet=hit.snippet,
            score=hit.score,
            retrieval_layer=retrieval_layer,  # type: ignore[arg-type]
        )

    @staticmethod
    def _count_chunk_scopes(chunks: list[RagEvidenceChunk]) -> tuple[int, int]:
        public_count = sum(1 for chunk in chunks if chunk.source_type == "public_policy")
        private_count = sum(1 for chunk in chunks if chunk.source_type in {"private_sample", "private_upload"})
        return public_count, private_count

    def _vector_store_health(self) -> VectorStoreHealth:
        try:
            return self.vector_store_adapter.healthcheck()
        except Exception as exc:  # noqa: BLE001
            return VectorStoreHealth(
                backend="current",
                status="degraded",
                available=False,
                reason=str(exc),
                metadata={"adapter_name": type(self.vector_store_adapter).__name__, "error_type": type(exc).__name__},
            )

    @staticmethod
    def _vector_adapter_name(health: VectorStoreHealth) -> str:
        adapter_name = health.metadata.get("adapter_name")
        return adapter_name if isinstance(adapter_name, str) and adapter_name else health.backend


def build_rag_query_params(
    *,
    question: str,
    knowledge_scope: RagKnowledgeScope,
    top_k: int = 5,
    mode: str | None = None,
    allowed_knowledge_item_ids: list[str] | set[str] | None = None,
    enable_rerank: bool = True,
    region: str | None = None,
    doc_type: str | None = None,
) -> RagQueryParams:
    settings = get_settings()
    requested_mode = mode or settings.rag_default_mode
    if requested_mode not in {"naive", "mix"}:
        requested_mode = "mix"
    return RagQueryParams(
        question=question,
        mode=requested_mode,  # type: ignore[arg-type]
        knowledge_scope=knowledge_scope,
        top_k=top_k,
        allowed_knowledge_item_ids=list(allowed_knowledge_item_ids or []),
        enable_rerank=enable_rerank,
        region=region,
        doc_type=doc_type,
    )


@lru_cache(maxsize=1)
def get_rag_engine_service() -> RagEngineService:
    return RagEngineService()
