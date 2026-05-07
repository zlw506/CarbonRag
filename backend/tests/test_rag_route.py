from fastapi.testclient import TestClient

from app.main import app
from app.rag.contracts import RetrievalTrace
from app.rag.schemas import RagEvidenceChunk, RagEvidenceReference, RagRetrievalMetadata, RagRetrievalResult
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


def test_rag_retrieve_route_returns_retrieval_only_data(monkeypatch) -> None:
    fake_engine = FakeRagEngine()
    monkeypatch.setattr("app.api.v1.endpoints.rag._sync_user_knowledge", lambda owner_user_id: None)
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
    monkeypatch.setattr("app.api.v1.endpoints.rag._sync_user_knowledge", lambda owner_user_id: None)
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


def test_rag_retrieve_route_requires_authenticated_user() -> None:
    client.cookies.clear()
    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "双碳政策依据有哪些？"},
    )
    assert response.status_code == 401


def test_rag_retrieve_route_rejects_blank_question(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.endpoints.rag._sync_user_knowledge", lambda owner_user_id: None)
    register_and_login(client, prefix="ragblank")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "   "},
    )

    assert response.status_code == 422
    assert "question cannot be blank" in response.text


def test_rag_retrieve_route_rejects_invalid_top_k(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.endpoints.rag._sync_user_knowledge", lambda owner_user_id: None)
    register_and_login(client, prefix="ragtopk")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "双碳政策依据有哪些？", "top_k": 0},
    )

    assert response.status_code == 422
    assert "top_k" in response.text


def test_rag_retrieve_route_returns_structured_runtime_error(monkeypatch) -> None:
    fake_engine = FakeRagEngine(raises=True)
    monkeypatch.setattr("app.api.v1.endpoints.rag._sync_user_knowledge", lambda owner_user_id: None)
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_engine_service", lambda: fake_engine)
    register_and_login(client, prefix="ragerror")

    response = client.post(
        "/api/v1/rag/retrieve",
        json={"question": "双碳政策依据有哪些？"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"]["error"] == "rag_retrieval_failed"
    assert payload["detail"]["message"] == "RAG retrieval failed."
    assert payload["detail"]["backend_detail"] == "fake rag engine failure"
