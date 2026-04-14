from dataclasses import dataclass

import httpx

from app.ai_runtime.providers.base import BaseChatProvider, ChatCompletionResult, ChatProviderError, ProviderDescriptor


@dataclass
class AnthropicChatProvider(BaseChatProvider):
    base_url: str
    api_key: str
    model_name: str
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: float = 30.0
    mode: str = "anthropic"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="anthropic-chat",
            provider_type="chat",
            mode=self.mode,
            default_model=self.model_name,
        )

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        try:
            response = httpx.post(
                f"{self.base_url.rstrip('/')}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_input}],
                },
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ChatProviderError("Anthropic 请求超时。", reason="timeout") from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError("Anthropic 请求失败。", reason="network_error") from exc

        if response.status_code >= 400:
            raise ChatProviderError(f"Anthropic 返回 HTTP {response.status_code}。", reason="http_error", status_code=response.status_code)

        payload = response.json()
        content = "".join(
            item.get("text", "")
            for item in payload.get("content", [])
            if isinstance(item, dict) and item.get("type") == "text"
        ).strip()
        if not content:
            raise ChatProviderError("Anthropic 返回空内容。", reason="empty_content")

        return ChatCompletionResult(
            content=content,
            metadata={
                "provider_mode": self.mode,
                "base_url": self.base_url,
                "model_name": self.model_name,
                "transport": "anthropic_messages",
            },
        )
