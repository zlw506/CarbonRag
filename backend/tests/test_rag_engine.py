from dataclasses import dataclass, field
from typing import Sequence

from app.ai_runtime.providers.base import (
    BaseEmbeddingProvider,
    BaseRerankProvider,
    EmbeddingResult,
    ProviderDescriptor,
    RerankItem,
    RerankResult,
)
from app.core.config import Settings
from app.rag.schemas import RagQueryParams
from app.rag.service import RagEngineService
from app.rag.vector import VectorSearchResult
from app.rag.vector_store import FakeVectorStoreAdapter
from app.retrieval.schemas import RetrievedChunk, RetrievalResult


def build_chunk(*, chunk_id: str, score: float = 1.0, source_type: str = "public_policy") -> RetrievedChunk:
    return RetrievedChunk(
        doc_id=chunk_id.split("_chunk_")[0],
        title=f"title-{chunk_id}",
        source_type=source_type,  # type: ignore[arg-type]
        source="test-source",
        chunk_id=chunk_id,
        snippet=f"snippet for {chunk_id}",
        score=score,
    )


@dataclass
class StaticRetriever:
    hits: list[RetrievedChunk]

    def search(self, *, question: str, top_k: int = 5, **kwargs) -> RetrievalResult:
        selected = self.hits[:top_k]
        return RetrievalResult(query=question, top_k=top_k, total_hits=len(selected), hits=selected)


@dataclass
class FakeVectorRetriever:
    chunks: list[RetrievedChunk]
    available: bool = True
    needs_embedding: bool = True
    seen_embedding: list[float] | None = None

    def is_available(self) -> bool:
        return self.available

    def requires_embedding(self) -> bool:
        return self.needs_embedding

    def search(
        self,
        *,
        question: str,
        query_embedding: list[float] | None,
        top_k: int,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> VectorSearchResult:
        self.seen_embedding = query_embedding
        return VectorSearchResult(
            chunks=self.chunks[:top_k],
            metadata={
                "question": question,
                "embedding_seen": query_embedding is not None,
                "allowed_knowledge_item_count": len(allowed_knowledge_item_ids or set()),
            },
        )


@dataclass
class FakeEmbeddingProvider(BaseEmbeddingProvider):
    calls: list[list[str]] = field(default_factory=list)

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(name="fake-embedding", provider_type="embedding", mode="fake")

    def embed_stub(self, texts: Sequence[str]) -> EmbeddingResult:
        self.calls.append(list(texts))
        return EmbeddingResult(vectors=[[0.25, 0.5, 0.75]], metadata={"fake": True})


@dataclass
class FakeRerankProvider(BaseRerankProvider):
    calls: int = 0

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(name="fake-rerank", provider_type="rerank", mode="fake")

    def rerank_stub(
        self,
        *,
        query: str,
        items: Sequence[RerankItem],
        top_k: int,
    ) -> RerankResult:
        self.calls += 1
        ranked_ids = [item.item_id for item in reversed(items)]
        return RerankResult(
            ranked_ids=ranked_ids[:top_k],
            scores={item_id: float(index) for index, item_id in enumerate(ranked_ids)},
            metadata={"status": "applied", "query": query},
        )


def build_service(
    *,
    settings: Settings,
    vector_retriever=None,
    embedding_provider=None,
    rerank_provider=None,
    fallback_hits: list[RetrievedChunk] | None = None,
    vector_store_adapter=None,
) -> RagEngineService:
    fallback = StaticRetriever(
        fallback_hits if fallback_hits is not None else [build_chunk(chunk_id="policy_001_chunk_01")]
    )
    return RagEngineService(
        settings=settings,
        vector_retriever=vector_retriever,
        embedding_provider=embedding_provider or FakeEmbeddingProvider(),
        rerank_provider=rerank_provider or FakeRerankProvider(),
        public_retriever=fallback,  # type: ignore[arg-type]
        private_retriever=fallback,  # type: ignore[arg-type]
        mixed_retriever=fallback,  # type: ignore[arg-type]
        vector_store_adapter=vector_store_adapter,
    )


def test_rag_engine_returns_structured_bm25_fallback_when_disabled() -> None:
    service = build_service(settings=Settings(rag_engine_enabled=False, rag_vector_enabled=False))

    result = service.retrieve(
        RagQueryParams(
            question="什么是双碳目标？",
            mode="mix",
            knowledge_scope="mixed",
            top_k=1,
        )
    )

    assert result.total_hits == 1
    assert result.chunks[0].retrieval_layer == "bm25_fallback"
    assert result.references[0].reference_id == "ref-1"
    assert result.metadata.vector_status == "disabled"
    assert result.metadata.vector_backend == "current"
    assert result.metadata.vector_backend_health == "ok"
    assert result.metadata.vector_adapter_name == "CurrentVectorStoreAdapter"
    assert result.metadata.graph_status == "unavailable"
    assert result.metadata.fallback_reason == "rag_engine_disabled"
    assert result.metadata.retriever_mode == "bm25_fallback"
    assert result.metadata.requested_top_k == 1
    assert result.metadata.returned_count == 1
    assert result.metadata.fallback_used is True
    assert result.metadata.latency_ms is not None
    assert result.metadata.public_chunk_count == 1
    assert result.metadata.private_chunk_count == 0
    assert result.metadata.strategy == "bm25_dense_hybrid"
    assert result.metadata.retrieval_path == [
        "vector:disabled",
        "graph:unavailable",
        "bm25_fallback",
        "rerank:disabled",
    ]
    assert result.metadata.trace.total_hits == 1
    assert result.metadata.trace.query == "什么是双碳目标？"
    assert result.metadata.trace.retriever_mode == "bm25_fallback"
    assert result.metadata.trace.requested_top_k == 1
    assert result.metadata.trace.returned_count == 1
    assert result.metadata.trace.fallback_used is True
    assert result.metadata.trace.chunk_ids == ["policy_001_chunk_01"]
    assert result.metadata.trace.citations[0].citation_id == "ref-1"
    assert result.metadata.trace.metadata["vector_backend"] == "current"
    assert "retrieval_layer" not in result.hits[0]


def test_rag_engine_uses_embedding_provider_for_available_vector_retrieval() -> None:
    embedding_provider = FakeEmbeddingProvider()
    vector_retriever = FakeVectorRetriever(chunks=[build_chunk(chunk_id="policy_002_chunk_01", score=3.0)])
    service = build_service(
        settings=Settings(rag_engine_enabled=True, rag_vector_enabled=True),
        vector_retriever=vector_retriever,
        embedding_provider=embedding_provider,
        fallback_hits=[],
    )

    result = service.retrieve(
        RagQueryParams(
            question="统计核算怎么做？",
            mode="naive",
            knowledge_scope="public",
            top_k=1,
        )
    )

    assert embedding_provider.calls == [["统计核算怎么做？"]]
    assert vector_retriever.seen_embedding == [0.25, 0.5, 0.75]
    assert result.chunks[0].retrieval_layer == "vector"
    assert result.metadata.vector_status == "queried"
    assert result.metadata.graph_status == "skipped"
    assert result.metadata.fallback_reason is None
    assert result.metadata.retriever_mode == "vector"
    assert result.metadata.returned_count == 1
    assert result.metadata.fallback_used is False


def test_rag_engine_reranks_through_ai_runtime_provider() -> None:
    rerank_provider = FakeRerankProvider()
    vector_retriever = FakeVectorRetriever(
        chunks=[
            build_chunk(chunk_id="policy_001_chunk_01", score=1.0),
            build_chunk(chunk_id="policy_002_chunk_01", score=0.5),
        ],
        needs_embedding=False,
    )
    service = build_service(
        settings=Settings(
            rag_engine_enabled=True,
            rag_vector_enabled=True,
            rag_rerank_enabled=True,
        ),
        vector_retriever=vector_retriever,
        rerank_provider=rerank_provider,
        fallback_hits=[],
    )

    result = service.retrieve(
        RagQueryParams(
            question="哪个政策更相关？",
            mode="mix",
            knowledge_scope="mixed",
            top_k=2,
            enable_rerank=True,
        )
    )

    assert rerank_provider.calls == 1
    assert [chunk.chunk_id for chunk in result.chunks] == ["policy_002_chunk_01", "policy_001_chunk_01"]
    assert result.metadata.rerank_status == "applied"
    assert result.metadata.provider_metadata["rerank"]["status"] == "applied"


def test_rag_engine_reports_zero_hit_metadata() -> None:
    service = build_service(
        settings=Settings(rag_engine_enabled=False, rag_vector_enabled=False),
        fallback_hits=[],
    )

    result = service.retrieve(
        RagQueryParams(
            question="没有匹配结果的问题",
            mode="mix",
            knowledge_scope="public",
            top_k=3,
        )
    )

    assert result.total_hits == 0
    assert result.chunks == []
    assert result.references == []
    assert result.metadata.requested_top_k == 3
    assert result.metadata.returned_count == 0
    assert result.metadata.fallback_used is True
    assert result.metadata.fallback_reason == "rag_engine_disabled"
    assert result.metadata.public_chunk_count == 0
    assert result.metadata.private_chunk_count == 0


def test_rag_engine_experimental_hybrid_returns_source_metadata() -> None:
    bm25_chunk = build_chunk(chunk_id="policy_001_chunk_01", score=2.0)
    vector_chunk = build_chunk(chunk_id="policy_001_chunk_01", score=0.8)
    service = build_service(
        settings=Settings(rag_engine_enabled=True, rag_vector_enabled=True),
        vector_store_adapter=FakeVectorStoreAdapter(chunks=[vector_chunk]),
        fallback_hits=[bm25_chunk],
    )

    result = service.retrieve(
        RagQueryParams(
            question="双碳政策依据有哪些？",
            mode="mix",
            knowledge_scope="mixed",
            top_k=2,
            retrieval_strategy="bm25_vector_hybrid",
        )
    )

    assert result.metadata.retrieval_strategy == "bm25_vector_hybrid"
    assert result.metadata.provider_metadata["retriever_strategy"]["strategy"] == "bm25_vector_hybrid"
    assert result.metadata.vector_status == "queried"
    assert result.metadata.vector_hit_count == 1
    assert result.chunks[0].chunk_id == "policy_001_chunk_01"
    assert result.chunks[0].source_retrievers == ["bm25", "vector"]
    assert result.chunks[0].from_bm25 is True
    assert result.chunks[0].from_vector is True
    assert result.chunks[0].merged_score is not None


def test_rag_engine_experimental_vector_unavailable_falls_back_to_bm25() -> None:
    bm25_chunk = build_chunk(chunk_id="policy_001_chunk_01", score=2.0)
    service = build_service(
        settings=Settings(rag_engine_enabled=True, rag_vector_enabled=True),
        vector_store_adapter=FakeVectorStoreAdapter(chunks=[], status="degraded", available=False),
        fallback_hits=[bm25_chunk],
    )

    result = service.retrieve(
        RagQueryParams(
            question="双碳政策依据有哪些？",
            mode="mix",
            knowledge_scope="mixed",
            top_k=1,
            retrieval_strategy="bm25_vector_hybrid",
        )
    )

    assert result.chunks[0].chunk_id == "policy_001_chunk_01"
    assert result.metadata.retrieval_strategy == "bm25_vector_hybrid"
    assert result.metadata.fallback_used is True
    assert result.metadata.fallback_reason == "fake_vector_store_unavailable"
    assert result.metadata.vector_status == "unavailable"
