import json
from dataclasses import dataclass
from typing import Any, Iterator

import httpx

from app.ai_runtime.providers.base import BaseChatProvider, ChatCompletionResult, ChatProviderError, ChatStreamEvent, ProviderDescriptor


@dataclass
class OllamaChatProvider(BaseChatProvider):
    base_url: str
    model_name: str
    timeout_seconds: float = 30.0
    mode: str = "ollama"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="ollama-chat",
            provider_type="chat",
            mode=self.mode,
            default_model=self.model_name,
        )

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        try:
            response = httpx.post(
                f"{self.base_url.rstrip('/')}/chat",
                json=self._build_payload(system_prompt=system_prompt, user_input=user_input, stream=False),
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ChatProviderError("Ollama 请求超时。", reason="timeout") from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError("Ollama 请求失败。", reason="network_error") from exc
        if response.status_code >= 400:
            raise ChatProviderError(f"Ollama 返回 HTTP {response.status_code}。", reason="http_error", status_code=response.status_code)

        payload = response.json()
        content = payload.get("message", {}).get("content", "").strip()
        if not content:
            raise ChatProviderError("Ollama 返回空内容。", reason="empty_content")

        return ChatCompletionResult(
            content=content,
            metadata={
                "provider_mode": self.mode,
                "base_url": self.base_url,
                "model_name": self.model_name,
                "transport": "ollama_chat_json",
            },
        )

    def stream_response(self, *, system_prompt: str, user_input: str) -> Iterator[ChatStreamEvent]:
        yield ChatStreamEvent(kind="status", data={"status": "thinking", "provider_mode": self.mode})
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url.rstrip('/')}/chat",
                json=self._build_payload(system_prompt=system_prompt, user_input=user_input, stream=True),
                timeout=self.timeout_seconds,
            ) as response:
                if response.status_code >= 400:
                    raise ChatProviderError(f"Ollama 返回 HTTP {response.status_code}。", reason="http_error", status_code=response.status_code)

                answer_fragments: list[str] = []
                answer_started = False
                for raw_line in response.iter_lines():
                    line = raw_line.decode("utf-8", errors="ignore") if isinstance(raw_line, bytes) else raw_line
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ChatProviderError("Ollama 返回了无法解析的流式片段。", reason="invalid_response") from exc
                    if chunk.get("error"):
                        raise ChatProviderError(str(chunk["error"]), reason="http_error")

                    delta = chunk.get("message", {}).get("content") or ""
                    if delta:
                        if not answer_started:
                            answer_started = True
                            yield ChatStreamEvent(kind="status", data={"status": "streaming", "provider_mode": self.mode})
                        answer_fragments.append(delta)
                        yield ChatStreamEvent(kind="answer_delta", data={"delta": delta})
                    if chunk.get("done"):
                        break
        except httpx.TimeoutException as exc:
            raise ChatProviderError("Ollama 请求超时。", reason="timeout") from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError("Ollama 请求失败。", reason="network_error") from exc

        content = "".join(answer_fragments).strip()
        if not content:
            raise ChatProviderError("Ollama 返回空内容。", reason="empty_content")

        yield ChatStreamEvent(
            kind="done",
            data={
                "answer": content,
                "content": content,
                "metadata": {
                    "provider_mode": self.mode,
                    "base_url": self.base_url,
                    "model_name": self.model_name,
                    "transport": "ollama_chat_stream",
                },
            },
        )

    def _build_payload(self, *, system_prompt: str, user_input: str, stream: bool) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "stream": stream,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
        }
