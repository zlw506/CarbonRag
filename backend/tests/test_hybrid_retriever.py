from app.rag.retriever_strategy import BM25Retriever, HybridRetriever, VectorRetriever
from app.rag.vector_store import FakeVectorStoreAdapter
from app.retrieval.schemas import RetrievedChunk


def build_chunk(*, chunk_id: str, score: float, title: str | None = None) -> RetrievedChunk:
    return RetrievedChunk(
        doc_id=chunk_id.split("_chunk_")[0],
        title=title or f"title-{chunk_id}",
        source_type="public_policy",
        source="test-source",
        chunk_id=chunk_id,
        snippet=f"snippet for {chunk_id}",
        score=score,
    )


def test_bm25_retriever_returns_source_metadata() -> None:
    chunk = build_chunk(chunk_id="policy_001_chunk_01", score=2.0)
    retriever = BM25Retriever(adapter=FakeVectorStoreAdapter(chunks=[chunk]))

    result = retriever.retrieve(query="carbon", top_k=1)

    assert result.strategy == "bm25_only"
    assert result.chunks == [chunk]
    assert result.metadata["bm25_hit_count"] == 1
    source = result.metadata["chunk_sources"][chunk.chunk_id]
    assert source["from_bm25"] is True
    assert source["from_vector"] is False
    assert source["source_retrievers"] == ["bm25"]


def test_vector_retriever_returns_source_metadata() -> None:
    chunk = build_chunk(chunk_id="policy_002_chunk_01", score=0.8)
    retriever = VectorRetriever(adapter=FakeVectorStoreAdapter(chunks=[chunk]))

    result = retriever.retrieve(query="carbon", top_k=1, query_embedding=[0.1, 0.2])

    assert result.strategy == "vector_only"
    assert result.chunks == [chunk]
    assert result.metadata["vector_status"] == "queried"
    assert result.metadata["vector_hit_count"] == 1
    source = result.metadata["chunk_sources"][chunk.chunk_id]
    assert source["from_bm25"] is False
    assert source["from_vector"] is True
    assert source["source_retrievers"] == ["vector"]


def test_hybrid_retriever_merges_and_deduplicates_chunks() -> None:
    duplicate_bm25 = build_chunk(chunk_id="policy_001_chunk_01", score=2.0)
    duplicate_vector = build_chunk(chunk_id="policy_001_chunk_01", score=0.9)
    vector_only = build_chunk(chunk_id="policy_002_chunk_01", score=0.45)
    hybrid = HybridRetriever(
        bm25_retriever=BM25Retriever(adapter=FakeVectorStoreAdapter(chunks=[duplicate_bm25])),
        vector_retriever=VectorRetriever(adapter=FakeVectorStoreAdapter(chunks=[duplicate_vector, vector_only])),
    )

    result = hybrid.retrieve(query="carbon", top_k=3, query_embedding=[0.1, 0.2])

    assert result.strategy == "bm25_vector_hybrid"
    assert [chunk.chunk_id for chunk in result.chunks] == ["policy_001_chunk_01", "policy_002_chunk_01"]
    source = result.metadata["chunk_sources"]["policy_001_chunk_01"]
    assert source["bm25_score"] == 2.0
    assert source["vector_score"] == 0.9
    assert source["from_bm25"] is True
    assert source["from_vector"] is True
    assert source["source_retrievers"] == ["bm25", "vector"]
    assert result.metadata["fallback_used"] is False


def test_hybrid_retriever_falls_back_to_bm25_when_vector_unavailable() -> None:
    chunk = build_chunk(chunk_id="policy_001_chunk_01", score=2.0)
    hybrid = HybridRetriever(
        bm25_retriever=BM25Retriever(adapter=FakeVectorStoreAdapter(chunks=[chunk])),
        vector_retriever=VectorRetriever(
            adapter=FakeVectorStoreAdapter(chunks=[], status="degraded", available=False)
        ),
    )

    result = hybrid.retrieve(query="carbon", top_k=2, query_embedding=[0.1, 0.2])

    assert [returned.chunk_id for returned in result.chunks] == ["policy_001_chunk_01"]
    assert result.metadata["fallback_used"] is True
    assert result.metadata["fallback_reason"] == "fake_vector_store_unavailable"
    assert result.metadata["vector_hit_count"] == 0
    assert result.metadata["chunk_sources"][chunk.chunk_id]["source_retrievers"] == ["bm25"]
