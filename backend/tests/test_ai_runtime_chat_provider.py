import httpx

from app.ai_runtime.providers.chat_openai_compatible import OpenAICompatibleChatProvider


class FakeStreamingResponse:
    def __init__(self, *, status_code: int, lines: list[str]) -> None:
        self.status_code = status_code
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def iter_lines(self):
        for line in self._lines:
            yield line


def test_chat_provider_aggregates_streaming_chunks(monkeypatch) -> None:
    captured: dict = {}

    def fake_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeStreamingResponse(
            status_code=200,
            lines=[
                'data: {"id":"chatcmpl-demo","choices":[{"delta":{"role":"assistant","content":"双碳目标是"}}]}',
                'data: {"id":"chatcmpl-demo","choices":[{"delta":{"role":"assistant","content":"碳达峰和碳中和。"}}],"usage":{"prompt_tokens":12,"completion_tokens":18}}',
                "data: [DONE]",
            ],
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", fake_stream)

    provider = OpenAICompatibleChatProvider(
        base_url="https://example.com/v1",
        api_key="demo-key",
        model_name="gpt-5.4",
        temperature=0.2,
        max_tokens=4096,
        timeout_seconds=30.0,
    )

    result = provider.generate_response(
        system_prompt="你是 CarbonRag 的 ask mode 问答助手。",
        user_input="什么是双碳目标？",
    )

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer demo-key"
    assert captured["json"]["model"] == "gpt-5.4"
    assert captured["json"]["stream"] is True
    assert captured["json"]["messages"][0]["role"] == "system"
    assert captured["json"]["messages"][1]["role"] == "user"
    assert result.content == "双碳目标是碳达峰和碳中和。"
    assert result.metadata["transport"] == "streaming_sse_aggregate"


def test_chat_provider_falls_back_to_non_stream_when_stream_is_empty(monkeypatch) -> None:
    def fake_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        return FakeStreamingResponse(
            status_code=200,
            lines=[
                'data: {"id":"chatcmpl-empty","choices":[{"delta":{"role":"assistant","content":null}}]}',
                "data: [DONE]",
            ],
        )

    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-fallback",
                "choices": [
                    {
                        "message": {
                            "content": "双碳目标是我国提出的碳达峰与碳中和战略目标。"
                        }
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 18},
            },
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", fake_stream)
    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.post", fake_post)

    provider = OpenAICompatibleChatProvider(
        base_url="https://example.com/v1",
        api_key="demo-key",
        model_name="gpt-5.4",
        temperature=0.2,
        max_tokens=4096,
        timeout_seconds=30.0,
    )

    result = provider.generate_response(
        system_prompt="你是 CarbonRag 的 ask mode 问答助手。",
        user_input="什么是双碳目标？",
    )

    assert result.content.startswith("双碳目标是我国提出的")
    assert result.metadata["transport"] == "chat_completions_json"
