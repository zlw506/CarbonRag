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


class FakeSettingsService:
    def __init__(self, chat_provider: BaseChatProvider) -> None:
        self.chat_provider = chat_provider

    def build_chat_provider(self, **kwargs):  # noqa: ANN003
        return SimpleNamespace(provider_ref="test:fake-provider"), self.chat_provider


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
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_settings_service", lambda: FakeSettingsService(service.chat_provider))
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


def test_kb_defaults_upload_status_answer_and_eval(monkeypatch, tmp_path) -> None:
    service = build_rag_service(tmp_path)
    monkeypatch.setattr("app.rag.spine.get_settings", lambda: SimpleNamespace(rag_vector_backend="memory"))
    monkeypatch.setattr("app.api.v1.endpoints.kb.get_rag_spine_service", lambda: service)
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_rag_spine_service", lambda: service)
    monkeypatch.setattr("app.api.v1.endpoints.rag.get_settings_service", lambda: FakeSettingsService(service.chat_provider))
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="rag-parity")
    kb_response = client.post("/api/v1/kb", json={"name": "青木验收库"})
    assert kb_response.status_code == 200, kb_response.text
    kb_payload = kb_response.json()
    assert kb_payload["embedding_model"] == "BAAI/bge-m3"
    assert kb_payload["chunk_size"] == 512
    assert kb_payload["chunk_overlap"] == 64
    assert kb_payload["rerank_top_n"] == 5
    assert kb_payload["retrieval_top_k"] == 20
    kb_id = kb_payload["kb_id"]

    upload_response = client.post(
        f"/api/v1/kb/{kb_id}/documents/upload",
        files={
            "file": (
                "qingmu.md",
                "# 青木制造\n\n青木制造合计外购电力为 217,650 kWh。绿色电力凭证编号为 GEC-QM-2025-02-0007。".encode("utf-8"),
                "text/markdown",
            )
        },
    )
    assert upload_response.status_code == 200, upload_response.text
    doc_payload = upload_response.json()
    assert doc_payload["filename"] == "qingmu.md"
    assert doc_payload["file_type"] == "md"
    assert doc_payload["file_size"] > 0
    assert doc_payload["file_path"]
    assert doc_payload["parse_progress"] == 0
    doc_id = doc_payload["doc_id"]

    status = client.get(f"/api/v1/kb/{kb_id}/documents/{doc_id}/status")
    assert status.status_code == 200, status.text
    assert status.json()["doc_id"] == doc_id

    assert client.post(f"/api/v1/kb/{kb_id}/documents/{doc_id}/parse").json()["parse_progress"] == 100
    assert client.post(f"/api/v1/kb/{kb_id}/documents/{doc_id}/chunk").json()["chunk_progress"] == 100
    indexed = client.post(f"/api/v1/kb/{kb_id}/documents/{doc_id}/index").json()
    assert indexed["index_status"] == "indexed"

    answer = client.post(
        "/api/v1/rag/answer",
        json={"kb_id": kb_id, "query": "青木制造合计外购电力是多少？", "mode": "hybrid", "top_k": 3},
    )
    assert answer.status_code == 200, answer.text
    answer_payload = answer.json()
    assert answer_payload["answer_mode"] == "llm_grounded"
    assert answer_payload["provider_name"] == "fake-chat"
    assert answer_payload["selected_chunks"]
    assert answer_payload["citations"]
    assert answer_payload["retrieval_trace"]["kb_id"] == kb_id

    eval_response = client.post(
        "/api/v1/rag/eval/run",
        json={
            "kb_id": kb_id,
            "mode": "hybrid",
            "top_k": 3,
            "cases": [
                {
                    "case_id": "qingmu-electricity-total",
                    "question": "青木制造合计外购电力是多少？",
                    "expected_chunk_keywords": ["217,650", "外购电力"],
                }
            ],
        },
    )
    assert eval_response.status_code == 200, eval_response.text
    eval_payload = eval_response.json()
    assert eval_payload["metrics"]["case_count"] == 1
    assert "hit_at_3" in eval_payload["metrics"]
    assert "answer_mode_rate" in eval_payload["metrics"]
    assert eval_payload["cases"][0]["case_id"] == "qingmu-electricity-total"


def test_kb_user_isolation(monkeypatch, tmp_path) -> None:
    service = build_rag_service(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.kb.get_rag_spine_service", lambda: service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="rag-owner")
    kb_id = client.post("/api/v1/kb", json={"name": "私有库"}).json()["kb_id"]

    register_and_login(client, prefix="rag-other")
    response = client.get(f"/api/v1/kb/{kb_id}")
    assert response.status_code == 404

