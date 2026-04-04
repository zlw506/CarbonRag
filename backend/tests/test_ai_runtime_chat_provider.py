import httpx

from app.ai_runtime.providers.chat_openai_compatible import OpenAICompatibleChatProvider


def test_chat_provider_posts_openai_compatible_payload(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-demo",
                "choices": [
                    {
                        "message": {
                            "content": "双碳目标是中国提出的碳达峰与碳中和战略目标。"
                        }
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 18},
            },
        )

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

    assert captured["url"] == "https://example.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer demo-key"
    assert captured["json"]["model"] == "gpt-5.4"
    assert captured["json"]["messages"][0]["role"] == "system"
    assert captured["json"]["messages"][1]["role"] == "user"
    assert result.content.startswith("双碳目标是")
