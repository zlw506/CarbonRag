import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ask_route_returns_200_for_success(monkeypatch) -> None:
    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        assert url.endswith("/chat/completions")
        assert json["messages"][1]["content"] == "什么是双碳目标？"
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-success",
                "choices": [{"message": {"content": "双碳目标包括碳达峰与碳中和两个目标。"}}],
            },
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.post", fake_post)

    response = client.post(
        "/api/v1/ask",
        json={
            "question": "什么是双碳目标？",
            "knowledge_scope": "public",
            "top_k": 5,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["mode"] == "ask"
    assert payload["status"] == "ok"
    assert payload["answer"].startswith("双碳目标")
    assert payload["citations"]
    assert payload["trace_id"].startswith("trace-")


def test_ask_route_returns_422_for_empty_question() -> None:
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "   ",
            "knowledge_scope": "public",
            "top_k": 5,
        },
    )
    payload = response.json()

    assert response.status_code == 422
    assert payload["mode"] == "ask"
    assert payload["status"] == "invalid_input"
    assert payload["trace_id"].startswith("trace-")


def test_ask_route_returns_422_for_private_sample_scope() -> None:
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "解释什么是双碳目标",
            "knowledge_scope": "private_sample",
            "top_k": 5,
        },
    )
    payload = response.json()

    assert response.status_code == 422
    assert payload["mode"] == "ask"
    assert payload["status"] == "invalid_input"
    assert payload["trace_id"].startswith("trace-")


def test_ask_route_returns_422_for_mixed_scope() -> None:
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "解释什么是双碳目标",
            "knowledge_scope": "mixed",
            "top_k": 5,
        },
    )
    payload = response.json()

    assert response.status_code == 422
    assert payload["mode"] == "ask"
    assert payload["status"] == "invalid_input"
    assert payload["trace_id"].startswith("trace-")


def test_ask_route_returns_502_for_provider_failure(monkeypatch) -> None:
    def failing_post(url: str, *, headers: dict, json: dict, timeout: float):
        raise httpx.ConnectError("provider down")

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.post", failing_post)

    response = client.post(
        "/api/v1/ask",
        json={
            "question": "什么是双碳目标？",
            "knowledge_scope": "public",
            "top_k": 5,
        },
    )
    payload = response.json()

    assert response.status_code == 502
    assert payload["mode"] == "ask"
    assert payload["status"] == "provider_error"
    assert payload["answer"] == "当前问答服务暂不可用，请稍后重试。"
    assert payload["trace_id"].startswith("trace-")
