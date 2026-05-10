from fastapi.testclient import TestClient
from types import SimpleNamespace

from app.ai_runtime.providers.base import BaseChatProvider, ChatCompletionResult, ProviderDescriptor
from app.main import app
from app.rag.kb.storage import RagKnowledgeStore
from app.rag.spine import RagSpineService
from tests.test_helpers import patch_test_auth_service, register_and_login

client = TestClient(app)


class FakeChatProvider(BaseChatProvider):
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="fake-chat",
            provider_type="test",
            mode="chat",
            default_model="fake-grounded-model",
        )

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        self.calls.append({"system_prompt": system_prompt, "user_input": user_input})
        return ChatCompletionResult(content="双碳目标包括碳达峰和碳中和。", metadata={"fake": True})


def build_rag_service(tmp_path):
    return RagSpineService(
        store=RagKnowledgeStore(sqlite_db_path=tmp_path / "carbonrag.sqlite3"),
        chat_provider=FakeChatProvider(),
    )


def test_kb_document_status_and_test_qa(monkeypatch, tmp_path) -> None:
    service = build_rag_service(tmp_path)
    monkeypatch.setattr("app.rag.spine.get_settings", lambda: SimpleNamespace(rag_vector_backend="memory"))
    monkeypatch.setattr("app.api.v1.endpoints.kb.get_rag_spine_service", lambda: service)
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_spine_service", lambda: service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="rag-spine")
    kb_response = client.post("/api/v1/kb", json={"name": "RAG-Pro 测试库"})
    assert kb_response.status_code == 200, kb_response.text
    kb_id = kb_response.json()["kb_id"]

    doc_response = client.post(
        f"/api/v1/kb/{kb_id}/documents",
        json={
            "title": "双碳目标测试文档",
            "text": "双碳目标包括碳达峰和碳中和。企业需要建立能源数据台账，并追踪用电量、燃气量和排放因子。",
        },
    )
    assert doc_response.status_code == 200, doc_response.text
    doc_id = doc_response.json()["doc_id"]

    assert client.post(f"/api/v1/kb/{kb_id}/documents/{doc_id}/parse").json()["status"] == "parsed"
    assert client.post(f"/api/v1/kb/{kb_id}/documents/{doc_id}/chunk").json()["status"] == "chunked"
    indexed = client.post(f"/api/v1/kb/{kb_id}/documents/{doc_id}/index").json()
    assert indexed["status"] == "indexed"
    assert indexed["indexed_chunk_count"] >= 1

    search = client.post(
        "/api/v1/rag/search",
        json={"kb_id": kb_id, "query": "企业如何追踪双碳目标？", "mode": "hybrid", "top_k": 3},
    )
    assert search.status_code == 200, search.text
    payload = search.json()
    assert payload["hits"]
    assert payload["trace"]["sparse_count"] >= 1
    assert payload["trace"]["merged_count"] >= 1
    assert payload["trace"]["vector_backend"] == "memory"

    qa = client.post(
        "/api/v1/rag/test-qa",
        json={"kb_id": kb_id, "query": "双碳目标包括什么？", "mode": "hybrid", "top_k": 3},
    )
    assert qa.status_code == 200, qa.text
    qa_payload = qa.json()
    assert qa_payload["run_id"]
    assert qa_payload["answer_mode"] == "llm_grounded"
    assert qa_payload["provider_name"] == "fake-chat"
    assert qa_payload["selected_chunks"]
    assert "双碳" in qa_payload["answer"]


def test_kb_user_isolation(monkeypatch, tmp_path) -> None:
    service = build_rag_service(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.kb.get_rag_spine_service", lambda: service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="rag-owner")
    kb_id = client.post("/api/v1/kb", json={"name": "私有库"}).json()["kb_id"]

    register_and_login(client, prefix="rag-other")
    response = client.get(f"/api/v1/kb/{kb_id}")
    assert response.status_code == 404

