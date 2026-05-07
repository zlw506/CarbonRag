from typing import Any

from app.core.config import Settings
from app.rag.contracts import ChunkRecord, EmbeddingRecord
from app.rag.schemas import RagQueryParams
from app.rag.service import RagEngineService
from app.rag.vector_store import (
    CurrentVectorStoreAdapter,
    PgVectorStoreAdapter,
    _build_pgvector_filter_clause,
    build_vector_store_adapter,
)
from app.retrieval.schemas import RetrievedChunk, RetrievalResult


class StaticSearchRetriever:
    def __init__(self, hits: list[RetrievedChunk]) -> None:
        self.chunks = hits

    def search(self, *, question: str, top_k: int = 5, **kwargs) -> RetrievalResult:
        del kwargs
        selected = self.chunks[:top_k]
        return RetrievalResult(query=question, top_k=top_k, total_hits=len(selected), hits=selected)


class InMemoryPgVectorStoreAdapter(PgVectorStoreAdapter):
    def __init__(self) -> None:
        super().__init__(database_url="postgresql://test")
        self.rows: list[dict[str, Any]] = []

    def _healthcheck(self) -> None:
        return None

    def _upsert_rows(self, rows: list[dict[str, Any]]) -> None:
        by_chunk_id = {row["chunk_id"]: row for row in self.rows}
        for row in rows:
            by_chunk_id[row["chunk_id"]] = row
        self.rows = list(by_chunk_id.values())

    def _search_rows(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        del query_embedding
        candidates = self.rows
        if filters.get("source_type"):
            candidates = [row for row in candidates if row["source_type"] == filters["source_type"]]
        if filters.get("document_id"):
            candidates = [row for row in candidates if row["document_id"] == filters["document_id"]]
        if filters.get("visibility"):
            candidates = [row for row in candidates if row["visibility"] == filters["visibility"]]
        return [{**row, "score": 0.95 - index * 0.05} for index, row in enumerate(candidates[:top_k])]

    def _delete_rows_by_document(self, *, document_id: str) -> int:
        before_count = len(self.rows)
        self.rows = [row for row in self.rows if row["document_id"] != document_id]
        return before_count - len(self.rows)


def _chunk_record(
    *,
    chunk_id: str,
    document_id: str,
    source_type: str = "private_sample",
    visibility: str = "personal",
) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        document_id=document_id,
        text=f"Text for {chunk_id}",
        source_type=source_type,  # type: ignore[arg-type]
        title=f"Title {document_id}",
        knowledge_item_id=f"knowledge-{document_id}",
        source="test-source",
        source_uri=f"https://example.com/{document_id}",
        metadata={"visibility": visibility, "library_scope": visibility},
    )


def _embedding(chunk_id: str) -> EmbeddingRecord:
    return EmbeddingRecord(
        embedding_id=f"embedding-{chunk_id}",
        chunk_id=chunk_id,
        model_name="fake-embedding",
        vector=[0.1, 0.2, 0.3],
    )


def test_pgvector_adapter_initialization_failure_is_safe() -> None:
    adapter = PgVectorStoreAdapter(database_url=None)

    health = adapter.healthcheck()
    search = adapter.search(query="test", query_embedding=[0.1], top_k=3)

    assert health.backend == "pgvector"
    assert health.status == "degraded"
    assert health.available is False
    assert health.reason == "pgvector_database_url_missing"
    assert search.backend == "pgvector"
    assert search.total_hits == 0
    assert search.metadata["status"] == "error"


def test_vector_backend_current_does_not_connect_pgvector() -> None:
    current = CurrentVectorStoreAdapter(
        public_retriever=StaticSearchRetriever([]),  # type: ignore[arg-type]
        private_retriever=StaticSearchRetriever([]),  # type: ignore[arg-type]
        mixed_retriever=StaticSearchRetriever([]),  # type: ignore[arg-type]
    )

    adapter = build_vector_store_adapter(
        settings=Settings(rag_vector_backend="current"),
        current_adapter=current,
    )

    assert adapter is current
    assert adapter.healthcheck().backend == "current"


def test_pgvector_adapter_search_returns_unified_result_structure() -> None:
    adapter = InMemoryPgVectorStoreAdapter()
    chunk = _chunk_record(chunk_id="doc-001-chunk-001", document_id="doc-001", source_type="private_sample")

    upsert = adapter.upsert_chunks(chunks=[chunk], embeddings=[_embedding(chunk.chunk_id)])
    result = adapter.search(query="energy", query_embedding=[0.1, 0.2, 0.3], top_k=1, filters={"source_type": "private_sample"})

    assert upsert.upserted_count == 1
    assert result.backend == "pgvector"
    assert result.adapter_name == "InMemoryPgVectorStoreAdapter"
    assert result.total_hits == 1
    assert result.metadata["vector_hit_count"] == 1
    assert result.chunks[0].chunk_id == chunk.chunk_id
    assert result.chunks[0].doc_id == chunk.document_id
    assert result.chunks[0].source_type == "private_sample"


def test_pgvector_private_empty_selection_fails_closed() -> None:
    where_sql, params = _build_pgvector_filter_clause(
        {"knowledge_scope": "private_sample", "allowed_knowledge_item_ids": []}
    )

    assert where_sql == "WHERE 1 = 0"
    assert params == []


def test_pgvector_mixed_empty_selection_is_public_only() -> None:
    where_sql, params = _build_pgvector_filter_clause(
        {"knowledge_scope": "mixed", "allowed_knowledge_item_ids": []}
    )

    assert where_sql == "WHERE source_type = %s"
    assert params == ["public_policy"]


def test_pgvector_delete_by_document_does_not_affect_other_documents() -> None:
    adapter = InMemoryPgVectorStoreAdapter()
    chunk_a = _chunk_record(chunk_id="doc-a-chunk-001", document_id="doc-a")
    chunk_b = _chunk_record(chunk_id="doc-b-chunk-001", document_id="doc-b")
    adapter.upsert_chunks(chunks=[chunk_a, chunk_b], embeddings=[_embedding(chunk_a.chunk_id), _embedding(chunk_b.chunk_id)])

    delete = adapter.delete_by_document(document_id="doc-a")
    remaining = adapter.search(query="energy", query_embedding=[0.1, 0.2, 0.3], top_k=5)

    assert delete.metadata["deleted_count"] == 1
    assert [chunk.chunk_id for chunk in remaining.chunks] == ["doc-b-chunk-001"]


def test_rag_engine_pgvector_unavailable_falls_back_to_current() -> None:
    fallback_chunk = RetrievedChunk(
        doc_id="policy_001",
        title="Policy 001",
        source_type="public_policy",
        source="State Council",
        chunk_id="policy_001_chunk_01",
        snippet="Carbon policy fallback chunk.",
        score=2.5,
    )
    fallback = StaticSearchRetriever([fallback_chunk])
    service = RagEngineService(
        settings=Settings(
            rag_engine_enabled=True,
            rag_vector_enabled=True,
            rag_vector_backend="pgvector",
            database_url=None,
        ),
        public_retriever=fallback,  # type: ignore[arg-type]
        private_retriever=fallback,  # type: ignore[arg-type]
        mixed_retriever=fallback,  # type: ignore[arg-type]
    )

    result = service.retrieve(
        RagQueryParams(
            question="carbon policy",
            mode="mix",
            knowledge_scope="mixed",
            top_k=1,
        )
    )

    assert result.chunks[0].retrieval_layer == "bm25_fallback"
    assert result.metadata.vector_backend == "pgvector"
    assert result.metadata.vector_backend_health == "degraded"
    assert result.metadata.vector_adapter_name == "PgVectorStoreAdapter"
    assert result.metadata.vector_hit_count == 0
    assert result.metadata.fallback_used is True
    assert result.metadata.fallback_reason == "pgvector_database_url_missing"
    assert result.metadata.provider_metadata["vector_store"]["backend"] == "pgvector"
