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
            default_model=self.model_name
        )

    def generate_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> ChatCompletionResult:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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

        content = self._extract_content(payload_json)
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
            },
        )

    @staticmethod
    def _extract_content(payload_json: dict[str, Any]) -> str:
        try:
            content = payload_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ChatProviderError(
                "Chat provider response is missing choices[0].message.content.",
                reason="invalid_response",
            ) from exc

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

        raise ChatProviderError(
            "Chat provider returned unsupported content shape.",
            reason="invalid_response",
        )
