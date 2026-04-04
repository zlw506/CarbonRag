import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ask_route_returns_real_citations(monkeypatch) -> None:
    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        assert url.endswith("/chat/completions")
        assert "公共政策片段" in json["messages"][0]["content"]
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-grounded",
                "choices": [{"message": {"content": "根据公共政策样本，双碳目标是指碳达峰和碳中和两个目标。"}}],
            },
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.post", fake_post)

    response = client.post(
        "/api/v1/ask",
        json={
            "question": "什么是双碳目标？",
            "knowledge_scope": "public",
            "top_k": 3,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["citations"]
    first_citation = payload["citations"][0]
    assert first_citation["doc_id"].startswith("policy_")
    assert first_citation["title"]
    assert first_citation["source"]
    assert first_citation["snippet"]
    assert first_citation["chunk_id"].startswith(first_citation["doc_id"])


def test_ask_route_returns_422_for_non_public_scope() -> None:
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "北京市双碳实施重点是什么？",
            "knowledge_scope": "mixed",
            "top_k": 3,
        },
    )
    payload = response.json()

    assert response.status_code == 422
    assert payload["status"] == "invalid_input"
    assert payload["citations"] == []


def test_ask_route_returns_502_with_structured_provider_error(monkeypatch) -> None:
    def failing_post(url: str, *, headers: dict, json: dict, timeout: float):
        raise httpx.ConnectError("provider down")

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.post", failing_post)

    response = client.post(
        "/api/v1/ask",
        json={
            "question": "什么是双碳目标？",
            "knowledge_scope": "public",
            "top_k": 3,
        },
    )
    payload = response.json()

    assert response.status_code == 502
    assert payload["mode"] == "ask"
    assert payload["status"] == "provider_error"
    assert payload["trace_id"].startswith("trace-")
