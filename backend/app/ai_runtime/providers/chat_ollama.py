from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from app.ai_runtime.providers.base import BaseChatProvider, ChatCompletionResult, ChatProviderError, ChatStreamEvent, ProviderDescriptor
from app.ai_runtime.providers.ollama_client import OllamaChatOptions, OllamaClient


@dataclass
class OllamaChatProvider(BaseChatProvider):
    base_url: str = "http://localhost:11434"
    model_name: str = "deepseek-r1:8b"
    temperature: float = 0.2
    timeout_seconds: float = 180.0
    max_retries: int = 1
    num_ctx: int | None = 8192
    keep_alive: str | None = "10m"
    think: bool | None = True
    mode: str = "ollama"

    def __post_init__(self) -> None:
        self.client = OllamaClient(base_url=self.base_url, timeout_seconds=self.timeout_seconds)
        self.base_url = self.client.base_url

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="ollama-chat",
            provider_type="chat",
            mode=self.mode,
            default_model=self.model_name,
        )

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        response = self.client.chat(
            model=self.model_name,
            messages=self._messages(system_prompt=system_prompt, user_input=user_input),
            stream=False,
            options=self._options(),
        )
        content = response.content.strip()
        if not content:
            raise ChatProviderError("Ollama 返回空内容。", reason="empty_content")
        return ChatCompletionResult(
            content=content,
            metadata={
                "provider_mode": self.mode,
                "provider_name": "ollama-chat",
                "base_url": self.base_url,
                "model_name": self.model_name,
                "transport": "ollama_native_chat_json",
                "thinking_content": response.thinking.strip() or None,
                "thinking_chunk_count": 1 if response.thinking.strip() else 0,
                "think_enabled": self.think,
                "num_ctx": self.num_ctx,
                "keep_alive": self.keep_alive,
            },
        )

    def stream_response(self, *, system_prompt: str, user_input: str) -> Iterator[ChatStreamEvent]:
        yield ChatStreamEvent(kind="status", data={"status": "thinking", "provider_mode": self.mode, "provider_name": "ollama-chat"})
        answer_fragments: list[str] = []
        thinking_fragments: list[str] = []
        answer_started = False
        saw_chunk = False

        for chunk in self.client.stream_chat(
            model=self.model_name,
            messages=self._messages(system_prompt=system_prompt, user_input=user_input),
            options=self._options(),
        ):
            saw_chunk = True
            message = chunk.get("message") if isinstance(chunk, dict) else None
            message = message if isinstance(message, dict) else {}
            thinking_delta = _normalize_text(message.get("thinking") or chunk.get("thinking"))
            answer_delta = _normalize_text(message.get("content"))
            if thinking_delta:
                thinking_fragments.append(thinking_delta)
                yield ChatStreamEvent(kind="thinking_delta", data={"delta": thinking_delta})
            if answer_delta:
                if not answer_started:
                    answer_started = True
                    yield ChatStreamEvent(kind="status", data={"status": "streaming", "provider_mode": self.mode, "provider_name": "ollama-chat"})
                answer_fragments.append(answer_delta)
                yield ChatStreamEvent(kind="answer_delta", data={"delta": answer_delta})
            if chunk.get("done"):
                break

        if not saw_chunk:
            raise ChatProviderError("Ollama 返回空流。", reason="invalid_response")
        content = "".join(answer_fragments).strip()
        if not content:
            raise ChatProviderError("Ollama 返回空内容。", reason="empty_content")
        thinking_content = "".join(thinking_fragments).strip() or None
        yield ChatStreamEvent(
            kind="done",
            data={
                "answer": content,
                "content": content,
                "metadata": {
                    "provider_mode": self.mode,
                    "provider_name": "ollama-chat",
                    "base_url": self.base_url,
                    "model_name": self.model_name,
                    "transport": "ollama_native_chat_stream",
                    "thinking_content": thinking_content,
                    "thinking_chunk_count": len(thinking_fragments),
                    "answer_chunk_count": len(answer_fragments),
                    "think_enabled": self.think,
                    "num_ctx": self.num_ctx,
                    "keep_alive": self.keep_alive,
                },
            },
        )

    def _options(self) -> OllamaChatOptions:
        return OllamaChatOptions(
            temperature=self.temperature,
            num_ctx=self.num_ctx,
            keep_alive=self.keep_alive,
            think=self.think,
        )

    @staticmethod
    def _messages(*, system_prompt: str, user_input: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)
