from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator

import httpx

from app.ai_runtime.providers.base import ChatProviderError


def normalize_ollama_base_url(base_url: str | None) -> str:
    """Return the Ollama server root, accepting either root, /api, or /v1 URLs."""

    normalized = (base_url or "http://localhost:11434").strip().rstrip("/")
    for suffix in ("/api", "/v1"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


@dataclass
class OllamaChatOptions:
    temperature: float | None = None
    num_ctx: int | None = None
    keep_alive: str | None = None
    think: bool | None = None


@dataclass
class OllamaChatResponse:
    content: str
    thinking: str = ""
    raw: dict[str, Any] | None = None


class OllamaClient:
    def __init__(self, *, base_url: str | None, timeout_seconds: float = 180.0) -> None:
        self.base_url = normalize_ollama_base_url(base_url)
        self.timeout_seconds = timeout_seconds

    @property
    def tags_url(self) -> str:
        return f"{self.base_url}/api/tags"

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}/api/chat"

    def list_models(self) -> list[str]:
        try:
            response = httpx.get(self.tags_url, timeout=min(self.timeout_seconds, 30.0))
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ChatProviderError("Ollama 模型列表请求超时。", reason="timeout") from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError("Ollama 模型列表请求失败。", reason="network_error") from exc
        payload = response.json()
        return [item["name"] for item in payload.get("models", []) if isinstance(item, dict) and item.get("name")]

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        stream: bool,
        options: OllamaChatOptions,
    ) -> OllamaChatResponse:
        payload = self.build_chat_payload(model=model, messages=messages, stream=stream, options=options)
        try:
            response = httpx.post(self.chat_url, json=payload, timeout=self.timeout_seconds)
        except httpx.TimeoutException as exc:
            raise ChatProviderError("Ollama 请求超时。", reason="timeout") from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError("Ollama 请求失败。", reason="network_error") from exc
        if response.status_code >= 400:
            raise ChatProviderError(f"Ollama 返回 HTTP {response.status_code}。", reason="http_error", status_code=response.status_code)
        data = response.json()
        message = data.get("message") if isinstance(data, dict) else None
        if not isinstance(message, dict):
            raise ChatProviderError("Ollama 响应缺少 message 字段。", reason="invalid_response")
        content = _normalize_text(message.get("content"))
        thinking = _normalize_text(message.get("thinking") or data.get("thinking"))
        return OllamaChatResponse(content=content, thinking=thinking, raw=data)

    def stream_chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        options: OllamaChatOptions,
    ) -> Iterator[dict[str, Any]]:
        payload = self.build_chat_payload(model=model, messages=messages, stream=True, options=options)
        try:
            with httpx.stream("POST", self.chat_url, json=payload, timeout=self.timeout_seconds) as response:
                if response.status_code >= 400:
                    raise ChatProviderError(f"Ollama 返回 HTTP {response.status_code}。", reason="http_error", status_code=response.status_code)
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
                    yield chunk
        except ChatProviderError:
            raise
        except httpx.TimeoutException as exc:
            raise ChatProviderError("Ollama 请求超时。", reason="timeout") from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError("Ollama 请求失败。", reason="network_error") from exc

    @staticmethod
    def build_chat_payload(
        *,
        model: str,
        messages: list[dict[str, str]],
        stream: bool,
        options: OllamaChatOptions,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        runtime_options: dict[str, Any] = {}
        if options.temperature is not None:
            runtime_options["temperature"] = options.temperature
        if options.num_ctx is not None:
            runtime_options["num_ctx"] = options.num_ctx
        if runtime_options:
            payload["options"] = runtime_options
        if options.keep_alive:
            payload["keep_alive"] = options.keep_alive
        if options.think is not None:
            payload["think"] = options.think
        return payload


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)
