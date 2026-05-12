from app.ai_runtime.providers.chat_ollama import OllamaChatProvider
from app.ai_runtime.providers.ollama_client import OllamaChatOptions, OllamaClient


def test_ollama_native_payload_includes_runtime_options() -> None:
    payload = OllamaClient.build_chat_payload(
        model="deepseek-r1:8b",
        messages=[{"role": "user", "content": "只回答 OK"}],
        stream=False,
        options=OllamaChatOptions(temperature=0.2, num_ctx=8192, keep_alive="10m", think=True),
    )

    assert payload["model"] == "deepseek-r1:8b"
    assert payload["stream"] is False
    assert payload["options"] == {"temperature": 0.2, "num_ctx": 8192}
    assert payload["keep_alive"] == "10m"
    assert payload["think"] is True


def test_ollama_provider_streams_thinking_and_answer() -> None:
    provider = OllamaChatProvider(base_url="http://localhost:11434/api", model_name="deepseek-r1:8b")
    provider.client = FakeOllamaClient()

    events = list(provider.stream_response(system_prompt="你是助手", user_input="测试"))

    assert any(event.kind == "thinking_delta" and event.data["delta"] == "先分析" for event in events)
    assert any(event.kind == "answer_delta" and event.data["delta"] == "OK" for event in events)
    done_event = events[-1]
    assert done_event.kind == "done"
    assert done_event.data["metadata"]["thinking_content"] == "先分析"
    assert done_event.data["metadata"]["model_name"] == "deepseek-r1:8b"


class FakeOllamaClient:
    base_url = "http://localhost:11434"

    def stream_chat(self, **kwargs):  # noqa: ANN003
        assert kwargs["model"] == "deepseek-r1:8b"
        yield {"message": {"thinking": "先分析", "content": ""}, "done": False}
        yield {"message": {"content": "OK"}, "done": False}
        yield {"message": {}, "done": True}
