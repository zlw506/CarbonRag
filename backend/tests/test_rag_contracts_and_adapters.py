from pathlib import Path

from app.rag.adapters import (
    chunk_record_from_retrieved_chunk,
    citation_ref_from_reference,
    retrieval_trace_from_result,
)
from app.rag.contracts import ChunkRecord, CitationRef
from app.rag.graph import DisabledGraphIndexBuilder
from app.rag.parser import LightweightParserProvider
from app.rag.schemas import RagEvidenceChunk, RagEvidenceReference, RagRetrievalMetadata, RagRetrievalResult
from app.rag.strategy import build_retrieval_path, plan_retrieval_strategy
from app.rag.vector_store import CurrentVectorStoreAdapter, DisabledVectorStoreAdapter, FakeVectorStoreAdapter
from app.rag.workflow import build_default_indexing_workflow
from app.retrieval.schemas import RetrievedChunk, RetrievalResult


class StaticSearchRetriever:
    def __init__(self, hits: list[RetrievedChunk]) -> None:
        self.chunks = hits

    def search(self, *, question: str, top_k: int = 5, **kwargs) -> RetrievalResult:
        del kwargs
        selected = self.chunks[:top_k]
        return RetrievalResult(query=question, top_k=top_k, total_hits=len(selected), hits=selected)


def test_public_chunk_record_maps_existing_retrieved_chunk() -> None:
    retrieved = RetrievedChunk(
        doc_id="policy_001",
        knowledge_item_id=None,
        title="Policy 001",
        source_type="public_policy",
        source="State Council",
        source_url="https://example.com/policy",
        chunk_id="policy_001_chunk_01",
        snippet="Carbon neutrality policy snippet.",
        score=2.5,
    )

    record = chunk_record_from_retrieved_chunk(retrieved)
    citation = CitationRef.from_chunk_record(reference_id="ref-1", chunk=record)

    assert record.document_id == "policy_001"
    assert record.text == "Carbon neutrality policy snippet."
    assert record.source_type == "public_policy"
    assert record.source_uri == "https://example.com/policy"
    assert record.content_hash
    assert record.metadata["score"] == 2.5
    assert citation.citation_id == "ref-1"
    assert citation.chunk_id == retrieved.chunk_id
    assert citation.quote == retrieved.snippet


def test_private_chunk_record_maps_existing_retrieved_chunk() -> None:
    retrieved = RetrievedChunk(
        doc_id="enterprise_doc_001",
        knowledge_item_id="knowledge-001",
        title="Enterprise Sample",
        source_type="private_sample",
        source="private-sample",
        source_url=None,
        sample_type="doc",
        business_topic="energy",
        library_scope="personal",
        chunk_id="enterprise_doc_001_chunk_01",
        snippet="Compressed air system energy use is a key issue.",
        score=1.75,
    )

    record = chunk_record_from_retrieved_chunk(retrieved)

    assert record.document_id == "enterprise_doc_001"
    assert record.knowledge_item_id == "knowledge-001"
    assert record.source_type == "private_sample"
    assert record.text == retrieved.snippet
    assert record.metadata["sample_type"] == "doc"
    assert record.metadata["business_topic"] == "energy"
    assert record.metadata["library_scope"] == "personal"


def test_reference_maps_to_citation_ref() -> None:
    chunk = RagEvidenceChunk(
        reference_id="ref-1",
        doc_id="policy_001",
        title="Policy 001",
        source_type="public_policy",
        source="State Council",
        source_url="https://example.com/policy",
        region="national",
        doc_type="policy",
        chunk_id="policy_001_chunk_01",
        snippet="Carbon neutrality policy snippet.",
        score=2.5,
        retrieval_layer="bm25_fallback",
    )
    reference = RagEvidenceReference(
        reference_id="ref-1",
        chunk_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        title=chunk.title,
        source_type=chunk.source_type,
        source=chunk.source,
        source_url=chunk.source_url,
    )

    citation = citation_ref_from_reference(reference, chunk=chunk)

    assert citation.citation_id == "ref-1"
    assert citation.reference_id == "ref-1"
    assert citation.document_id == "policy_001"
    assert citation.chunk_id == "policy_001_chunk_01"
    assert citation.source_uri == "https://example.com/policy"
    assert citation.quote == "Carbon neutrality policy snippet."


def test_retrieval_result_maps_to_unified_retrieval_trace() -> None:
    chunk = RagEvidenceChunk(
        reference_id="ref-1",
        doc_id="policy_001",
        title="Policy 001",
        source_type="public_policy",
        source="State Council",
        source_url="https://example.com/policy",
        chunk_id="policy_001_chunk_01",
        snippet="Carbon neutrality policy snippet.",
        score=2.5,
        retrieval_layer="bm25_fallback",
    )
    reference = RagEvidenceReference(
        reference_id="ref-1",
        chunk_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        title=chunk.title,
        source_type=chunk.source_type,
        source=chunk.source,
        source_url=chunk.source_url,
    )
    result = RagRetrievalResult(
        query="双碳政策依据有哪些？",
        total_hits=1,
        chunks=[chunk],
        references=[reference],
        metadata=RagRetrievalMetadata(
            mode="mix",
            knowledge_scope="public",
            top_k=3,
            chunk_top_k=3,
            retrieval_only=True,
            retriever_mode="bm25_fallback",
            requested_top_k=3,
            returned_count=1,
            fallback_used=True,
            vector_status="disabled",
            graph_status="unavailable",
            rerank_status="disabled",
            fallback_reason="rag_engine_disabled",
            latency_ms=1.5,
        ),
    )

    trace = retrieval_trace_from_result(result)

    assert trace.trace_id
    assert trace.query == "双碳政策依据有哪些？"
    assert trace.retriever_mode == "bm25_fallback"
    assert trace.requested_top_k == 3
    assert trace.returned_count == 1
    assert trace.fallback_used is True
    assert trace.fallback_reason == "rag_engine_disabled"
    assert trace.latency_ms == 1.5
    assert trace.chunk_ids == ["policy_001_chunk_01"]
    assert trace.citations[0].citation_id == "ref-1"


def test_lightweight_parser_provider_wraps_existing_parser(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("# 标题\n\n这是一段用于验证解析边界的 CarbonRag 文档内容。", encoding="utf-8")
    provider = LightweightParserProvider()

    parsed = provider.parse(path=source, mime_type="text/markdown")

    assert provider.supports(mime_type="text/markdown", name=source.name)
    assert parsed.parser_name == "carbonrag-lightweight"
    assert parsed.quality_score > 0
    assert parsed.document_id.startswith("parsed-")
    assert parsed.source_uri == str(source)
    assert parsed.source_type == "local_file"
    assert parsed.blocks
    assert parsed.blocks[0].block_type == "title"
    assert parsed.blocks[0].document_id == parsed.document_id


def test_disabled_vector_store_adapter_is_safe_by_default() -> None:
    adapter = DisabledVectorStoreAdapter()

    health = adapter.healthcheck()
    search = adapter.search(question="test", query_embedding=[0.1], top_k=3)
    upsert = adapter.upsert_chunks(chunks=[], embeddings=[])

    assert health.available is False
    assert health.status == "disabled"
    assert search.chunks == []
    assert search.metadata["embedding_seen"] is True
    assert upsert.upserted_count == 0


def test_fake_vector_store_adapter_search_returns_fixed_chunks() -> None:
    chunk = RetrievedChunk(
        doc_id="fake_doc_001",
        knowledge_item_id="knowledge-001",
        title="Fake Doc",
        source_type="private_sample",
        source="fake",
        chunk_id="fake_doc_001_chunk_01",
        snippet="Fixed fake chunk.",
        score=1.0,
    )
    adapter = FakeVectorStoreAdapter(chunks=[chunk])

    result = adapter.search(query="test query", top_k=1)

    assert result.backend == "fake"
    assert result.adapter_name == "FakeVectorStoreAdapter"
    assert result.total_hits == 1
    assert result.chunks == [chunk]
    assert result.metadata["query"] == "test query"


def test_current_vector_store_adapter_wraps_existing_public_search() -> None:
    chunk = RetrievedChunk(
        doc_id="policy_001",
        title="Policy 001",
        source_type="public_policy",
        source="State Council",
        chunk_id="policy_001_chunk_01",
        snippet="Carbon neutrality policy snippet.",
        score=2.5,
    )
    public_retriever = StaticSearchRetriever([chunk])
    private_retriever = StaticSearchRetriever([])
    mixed_retriever = StaticSearchRetriever([chunk])
    adapter = CurrentVectorStoreAdapter(
        public_retriever=public_retriever,  # type: ignore[arg-type]
        private_retriever=private_retriever,  # type: ignore[arg-type]
        mixed_retriever=mixed_retriever,  # type: ignore[arg-type]
    )

    direct = public_retriever.search(question="carbon", top_k=1, knowledge_scope="public")
    wrapped = adapter.search(question="carbon", top_k=1, filters={"knowledge_scope": "public"})

    assert wrapped.backend == "current"
    assert wrapped.adapter_name == "CurrentVectorStoreAdapter"
    assert wrapped.total_hits == direct.total_hits
    assert wrapped.chunks == direct.hits
    assert wrapped.metadata["storage"] == "in_memory_bm25"


def test_vector_store_healthcheck_reports_ok_and_degraded() -> None:
    current = CurrentVectorStoreAdapter(
        public_retriever=StaticSearchRetriever([]),  # type: ignore[arg-type]
        private_retriever=StaticSearchRetriever([]),  # type: ignore[arg-type]
        mixed_retriever=StaticSearchRetriever([]),  # type: ignore[arg-type]
    )
    degraded = FakeVectorStoreAdapter(status="degraded", available=False)

    assert current.healthcheck().status == "ok"
    assert current.healthcheck().available is True
    assert degraded.healthcheck().status == "degraded"
    assert degraded.healthcheck().available is False


def test_retrieval_strategy_and_path_are_explicit() -> None:
    plan = plan_retrieval_strategy(mode="mix", knowledge_scope="mixed")
    path = build_retrieval_path(
        retrieval_layer="bm25_fallback",
        vector_status="disabled",
        graph_status="unavailable",
        rerank_status="disabled",
    )

    assert plan.name == "bm25_dense_hybrid"
    assert "graph" in plan.planned_layers
    assert path == ["vector:disabled", "graph:unavailable", "bm25_fallback", "rerank:disabled"]


def test_graph_and_workflow_skeletons_are_dependency_light() -> None:
    graph_builder = DisabledGraphIndexBuilder()
    workflow = build_default_indexing_workflow(knowledge_item_id="item-001")

    assert graph_builder.is_available() is False
    assert graph_builder.build(chunks=[]).status == "disabled"
    assert graph_builder.search_candidates(question="test", top_k=3) == []
    assert workflow.knowledge_item_id == "item-001"
    assert [node.node_id for node in workflow.nodes] == ["parse", "chunk", "vector", "graph", "indexed"]
