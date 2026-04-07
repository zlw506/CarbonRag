import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.ai_runtime.providers.base import (
    BaseChatProvider,
    ChatCompletionResult,
    ChatProviderError,
    ProviderDescriptor,
)


@dataclass
class OpenAICompatibleChatProvider(BaseChatProvider):
    base_url: str
    api_key: str
    model_name: str = "gpt-5.4"
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: float = 30.0
    mode: str = "openai_compatible"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="openai-compatible-chat",
            provider_type="chat",
            mode=self.mode,
            default_model=self.model_name,
        )

    def generate_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> ChatCompletionResult:
        try:
            return self._generate_streaming_response(
                system_prompt=system_prompt,
                user_input=user_input,
            )
        except ChatProviderError as stream_exc:
            if stream_exc.reason not in {"invalid_response", "empty_content"}:
                raise

        return self._generate_non_stream_response(
            system_prompt=system_prompt,
            user_input=user_input,
        )

    def _generate_streaming_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> ChatCompletionResult:
        url = self._chat_completions_url
        payload = self._build_payload(
            system_prompt=system_prompt,
            user_input=user_input,
            stream=True,
        )
        headers = self._build_headers()

        try:
            with httpx.stream(
                "POST",
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            ) as response:
                if response.status_code >= 400:
                    raise ChatProviderError(
                        f"Chat provider returned HTTP {response.status_code}.",
                        reason="http_error",
                        status_code=response.status_code,
                    )

                fragments: list[str] = []
                response_id: str | None = None
                usage: dict[str, Any] = {}
                saw_data = False

                for raw_line in response.iter_lines():
                    line = raw_line.decode("utf-8", errors="ignore") if isinstance(raw_line, bytes) else raw_line
                    if not line:
                        continue
                    if line.startswith("event:") or line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        continue

                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break

                    saw_data = True
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError as exc:
                        raise ChatProviderError(
                            "Chat provider returned malformed streaming chunks.",
                            reason="invalid_response",
                            status_code=response.status_code,
                        ) from exc

                    if response_id is None:
                        response_id = chunk.get("id")
                    if isinstance(chunk.get("usage"), dict):
                        usage = chunk["usage"]

                    fragments.extend(self._extract_stream_delta_text(chunk))

        except httpx.TimeoutException as exc:
            raise ChatProviderError(
                "Chat provider request timed out.",
                reason="timeout",
            ) from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError(
                "Chat provider request failed.",
                reason="network_error",
            ) from exc

        if not saw_data:
            raise ChatProviderError(
                "Chat provider returned an empty streaming response.",
                reason="invalid_response",
            )

        content = "".join(fragments).strip()
        if not content:
            raise ChatProviderError(
                "Chat provider returned empty content.",
                reason="empty_content",
            )

        return ChatCompletionResult(
            content=content,
            metadata={
                "provider_mode": self.mode,
                "base_url": self.base_url,
                "model_name": self.model_name,
                "response_id": response_id,
                "usage": usage,
                "transport": "streaming_sse_aggregate",
            },
        )

    def _generate_non_stream_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> ChatCompletionResult:
        url = self._chat_completions_url
        payload = self._build_payload(
            system_prompt=system_prompt,
            user_input=user_input,
            stream=False,
        )
        headers = self._build_headers()

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
        except httpx.TimeoutException as exc:
            raise ChatProviderError(
                "Chat provider request timed out.",
                reason="timeout",
            ) from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError(
                "Chat provider request failed.",
                reason="network_error",
            ) from exc

        if response.status_code >= 400:
            raise ChatProviderError(
                f"Chat provider returned HTTP {response.status_code}.",
                reason="http_error",
                status_code=response.status_code,
            )

        try:
            payload_json = response.json()
        except ValueError as exc:
            raise ChatProviderError(
                "Chat provider returned non-JSON content.",
                reason="invalid_response",
                status_code=response.status_code,
            ) from exc

        content = self._extract_non_stream_content(payload_json)
        if not content:
            raise ChatProviderError(
                "Chat provider returned empty content.",
                reason="empty_content",
                status_code=response.status_code,
            )

        return ChatCompletionResult(
            content=content,
            metadata={
                "provider_mode": self.mode,
                "base_url": self.base_url,
                "model_name": self.model_name,
                "response_id": payload_json.get("id"),
                "usage": payload_json.get("usage", {}),
                "transport": "chat_completions_json",
            },
        )

    @property
    def _chat_completions_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        *,
        system_prompt: str,
        user_input: str,
        stream: bool,
    ) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }

    @staticmethod
    def _extract_non_stream_content(payload_json: dict[str, Any]) -> str:
        try:
            content = payload_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ChatProviderError(
                "Chat provider response is missing choices[0].message.content.",
                reason="invalid_response",
            ) from exc

        return OpenAICompatibleChatProvider._normalize_content(content)

    @staticmethod
    def _extract_stream_delta_text(chunk: dict[str, Any]) -> list[str]:
        try:
            delta = chunk["choices"][0]["delta"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ChatProviderError(
                "Streaming chat chunk is missing choices[0].delta.",
                reason="invalid_response",
            ) from exc

        content = delta.get("content")
        normalized = OpenAICompatibleChatProvider._normalize_stream_content(content)
        return [normalized] if normalized else []

    @staticmethod
    def _normalize_content(content: Any) -> str:
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            fragments: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        fragments.append(text.strip())
            return "\n".join(fragments).strip()

        if content is None:
            return ""

        raise ChatProviderError(
            "Chat provider returned unsupported content shape.",
            reason="invalid_response",
        )

    @staticmethod
    def _normalize_stream_content(content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            fragments: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        fragments.append(text)
            return "".join(fragments)

        if content is None:
            return ""

        raise ChatProviderError(
            "Chat provider returned unsupported streaming content shape.",
            reason="invalid_response",
        )
