from fastapi.testclient import TestClient

from app.main import app
from app.rag.contracts import RetrievalTrace
from app.rag.schemas import RagEvidenceChunk, RagEvidenceReference, RagRetrievalMetadata, RagRetrievalResult
from app.rag.service import RagEngineService
from app.retrieval.mixed_retriever import MixedScopeRetriever
from app.retrieval.schemas import RetrievedChunk, RetrievalResult
from tests.test_helpers import register_and_login

client = TestClient(app)


class FakeRagEngine:
    def __init__(self, *, hit_count: int = 1, raises: bool = False) -> None:
        self.last_params = None
        self.hit_count = hit_count
        self.raises = raises

    def retrieve(self, params):
        self.last_params = params
        if self.raises:
            raise RuntimeError("fake rag engine failure")
        chunks = []
        if self.hit_count > 0:
            chunks.append(
                RagEvidenceChunk(
                    reference_id="ref-1",
                    doc_id="policy_001",
                    title="Policy 001",
                    source_type="public_policy",
                    source="test-source",
                    source_url="https://example.com/policy",
                    chunk_id="policy_001_chunk_01",
                    snippet="policy snippet",
                    score=1.0,
                    retrieval_layer="bm25_fallback",
                    bm25_score=1.0 if params.retrieval_strategy else None,
                    merged_score=1.0 if params.retrieval_strategy else None,
                    from_bm25=True if params.retrieval_strategy else None,
                    from_vector=False if params.retrieval_strategy else None,
                    source_retrievers=["bm25"] if params.retrieval_strategy else [],
                )
            )
        return RagRetrievalResult(
            query=params.question,
            total_hits=len(chunks),
            chunks=chunks,
            references=[
                RagEvidenceReference(
                    reference_id="ref-1",
                    chunk_id=chunks[0].chunk_id,
                    doc_id=chunks[0].doc_id,
                    title=chunks[0].title,
                    source_type=chunks[0].source_type,
                    source=chunks[0].source,
                    source_url=chunks[0].source_url,
                )
            ]
            if chunks
            else [],
            metadata=RagRetrievalMetadata(
                mode=params.mode,
                knowledge_scope=params.knowledge_scope,
                top_k=params.top_k,
                chunk_top_k=params.chunk_top_k or params.top_k,
                retrieval_only=True,
                retriever_mode="bm25_fallback",
                requested_top_k=params.top_k,
                returned_count=len(chunks),
                fallback_used=True,
                vector_status="disabled",
                vector_backend="current",
                vector_backend_health="ok",
                vector_adapter_name="CurrentVectorStoreAdapter",
                retrieval_strategy=params.retrieval_strategy,
                graph_mode=params.graph_mode,
                graph_status="unavailable",
                rerank_status="disabled",
                fallback_reason="rag_engine_disabled",
                latency_ms=1.25,
                public_chunk_count=len(chunks),
                private_chunk_count=0,
                trace=RetrievalTrace(
                    query=params.question,
                    retriever_mode="bm25_fallback",
                    requested_top_k=params.top_k,
                    returned_count=len(chunks),
                    fallback_used=True,
                    fallback_reason="rag_engine_disabled",
                    latency_ms=1.25,
                    total_hits=len(chunks),
                    chunk_ids=[chunk.chunk_id for chunk in chunks],
                ),
            ),
        )


class StaticSearchRetriever:
    def __init__(self, hits: list[RetrievedChunk]) -> None:
        self.chunks = hits

    def search(self, *, question: str, top_k: int = 5, **kwargs) -> RetrievalResult:
        del kwargs
        selected = self.chunks[:top_k]
        return RetrievalResult(query=question, top_k=top_k, total_hits=len(selected), hits=selected)


class LeakyPrivateSearchRetriever(StaticSearchRetriever):
    def search(
        self,
        *,
        question: str,
        top_k: int = 5,
        allowed_knowledge_item_ids: set[str] | None = None,
        allowed_doc_ids: set[str] | None = None,
        **kwargs,
    ) -> RetrievalResult:
        del kwargs
        if allowed_knowledge_item_ids is not None:
            allowed_ids = allowed_knowledge_item_ids
        elif allowed_doc_ids is not None:
            allowed_ids = allowed_doc_ids
        else:
            allowed_ids = None
        candidates = self.chunks
        if allowed_ids is not None:
            candidates = [chunk for chunk in candidates if chunk.knowledge_item_id in allowed_ids]
        selected = candidates[:top_k]
        return RetrievalResult(query=question, top_k=top_k, total_hits=len(selected), hits=selected)


def _private_upload_chunk(*, knowledge_item_id: str = "user-a-upload") -> RetrievedChunk:
    return RetrievedChunk(
        doc_id=knowledge_item_id,
        knowledge_item_id=knowledge_item_id,
        title="User A personal upload",
        source_type="private_upload",
        source="user-a-upload.md",
        chunk_id=f"{knowledge_item_id}-chunk-001",
        snippet="User A confidential carbon inventory evidence.",
        score=3.0,
    )


def _public_policy_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        doc_id="policy-public",
        title="Public carbon policy",
        source_type="public_policy",
        source="public-policy.md",
        chunk_id="policy-public-chunk-001",
        snippet="Public carbon peak policy evidence.",
        score=2.0,
    )


def test_rag_retrieve_route_returns_retrieval_only_data(monkeypatch) -> None:
    fake_engine = FakeRagEngine()
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_engine_service", lambda: fake_engine)
    register_and_login(client, prefix="ragroute")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={
            "question": "双碳政策依据有哪些？",
            "mode": "mix",
            "knowledge_scope": "public",
            "top_k": 3,
            "allowed_knowledge_item_ids": ["ignored-for-public"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "双碳政策依据有哪些？"
    assert payload["chunks"][0]["retrieval_layer"] == "bm25_fallback"
    assert payload["references"][0]["reference_id"] == "ref-1"
    assert payload["metadata"]["retrieval_only"] is True
    assert payload["metadata"]["retriever_mode"] == "bm25_fallback"
    assert payload["metadata"]["requested_top_k"] == 3
    assert payload["metadata"]["returned_count"] == 1
    assert payload["metadata"]["fallback_used"] is True
    assert payload["metadata"]["fallback_reason"] == "rag_engine_disabled"
    assert payload["metadata"]["latency_ms"] == 1.25
    assert payload["metadata"]["public_chunk_count"] == 1
    assert payload["metadata"]["private_chunk_count"] == 0
    assert payload["metadata"]["vector_backend"] == "current"
    assert payload["metadata"]["vector_backend_health"] == "ok"
    assert payload["metadata"]["vector_adapter_name"] == "CurrentVectorStoreAdapter"
    assert payload["metadata"]["trace"]["trace_id"]
    assert payload["metadata"]["trace"]["query"] == "双碳政策依据有哪些？"
    assert payload["metadata"]["trace"]["retriever_mode"] == "bm25_fallback"
    assert payload["metadata"]["trace"]["chunk_ids"] == ["policy_001_chunk_01"]
    assert fake_engine.last_params.allowed_knowledge_item_ids == []


def test_rag_retrieve_route_returns_zero_hit_metadata(monkeypatch) -> None:
    fake_engine = FakeRagEngine(hit_count=0)
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_engine_service", lambda: fake_engine)
    register_and_login(client, prefix="ragzero")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "完全不存在的检索词", "mode": "mix", "knowledge_scope": "public", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks"] == []
    assert payload["references"] == []
    assert payload["metadata"]["returned_count"] == 0


def test_rag_retrieve_route_accepts_experimental_strategy(monkeypatch) -> None:
    fake_engine = FakeRagEngine()
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_engine_service", lambda: fake_engine)
    register_and_login(client, prefix="ragstrategy")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={
            "question": "双碳政策依据有哪些？",
            "mode": "mix",
            "knowledge_scope": "public",
            "top_k": 3,
            "retrieval_strategy": "bm25_vector_hybrid",
            "graph_mode": "graph_local",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert fake_engine.last_params.retrieval_strategy == "bm25_vector_hybrid"
    assert fake_engine.last_params.graph_mode == "graph_local"
    assert payload["chunks"][0]["source_retrievers"] == ["bm25"]
    assert payload["chunks"][0]["from_bm25"] is True
    assert payload["metadata"]["retrieval_strategy"] == "bm25_vector_hybrid"
    assert payload["metadata"]["graph_mode"] == "graph_local"


def test_rag_retrieve_route_requires_authenticated_user() -> None:
    client.cookies.clear()
    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "双碳政策依据有哪些？"},
    )
    assert response.status_code == 401


def test_rag_retrieve_route_rejects_blank_question() -> None:
    register_and_login(client, prefix="ragblank")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "   "},
    )

    assert response.status_code == 422
    assert "question cannot be blank" in response.text


def test_rag_retrieve_route_rejects_invalid_top_k() -> None:
    register_and_login(client, prefix="ragtopk")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "双碳政策依据有哪些？", "top_k": 0},
    )

    assert response.status_code == 422
    assert "top_k" in response.text


def test_rag_retrieve_route_returns_structured_runtime_error(monkeypatch) -> None:
    fake_engine = FakeRagEngine(raises=True)
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_engine_service", lambda: fake_engine)
    register_and_login(client, prefix="ragerror")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "双碳政策依据有哪些？"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"]["error"] == "rag_retrieval_failed"
    assert payload["detail"]["error_code"] == "rag_retrieval_failed"
    assert payload["detail"]["message"] == "RAG retrieval failed. Please retry later."
    assert "backend_detail" not in payload["detail"]
    assert "exception_type" not in payload["detail"]
    assert "fake rag engine failure" not in response.text


def test_rag_retrieve_private_empty_selection_does_not_leak_other_user_upload(monkeypatch) -> None:
    private_retriever = LeakyPrivateSearchRetriever([_private_upload_chunk()])
    rag_service = RagEngineService(
        public_retriever=StaticSearchRetriever([]),  # type: ignore[arg-type]
        private_retriever=private_retriever,  # type: ignore[arg-type]
        mixed_retriever=MixedScopeRetriever(
            public_retriever=StaticSearchRetriever([]),  # type: ignore[arg-type]
            private_retriever=private_retriever,  # type: ignore[arg-type]
        ),
    )
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_engine_service", lambda: rag_service)
    register_and_login(client, prefix="raguserbprivate")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={
            "question": "carbon inventory evidence",
            "knowledge_scope": "private_sample",
            "allowed_knowledge_item_ids": [],
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks"] == []
    assert payload["metadata"]["private_chunk_count"] == 0


def test_rag_retrieve_mixed_empty_selection_returns_public_only(monkeypatch) -> None:
    private_retriever = LeakyPrivateSearchRetriever([_private_upload_chunk()])
    rag_service = RagEngineService(
        public_retriever=StaticSearchRetriever([_public_policy_chunk()]),  # type: ignore[arg-type]
        private_retriever=private_retriever,  # type: ignore[arg-type]
        mixed_retriever=MixedScopeRetriever(
            public_retriever=StaticSearchRetriever([_public_policy_chunk()]),  # type: ignore[arg-type]
            private_retriever=private_retriever,  # type: ignore[arg-type]
        ),
    )
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_engine_service", lambda: rag_service)
    register_and_login(client, prefix="raguserbmixed")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={
            "question": "carbon policy evidence",
            "knowledge_scope": "mixed",
            "allowed_knowledge_item_ids": [],
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [chunk["source_type"] for chunk in payload["chunks"]] == ["public_policy"]
    assert payload["metadata"]["public_chunk_count"] == 1
    assert payload["metadata"]["private_chunk_count"] == 0
    assert all(chunk["knowledge_item_id"] != "user-a-upload" for chunk in payload["chunks"])
