from dataclasses import dataclass

import httpx

from app.ai_runtime.providers.base import BaseChatProvider, ChatCompletionResult, ChatProviderError, ProviderDescriptor


@dataclass
class GeminiChatProvider(BaseChatProvider):
    base_url: str
    api_key: str
    model_name: str
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: float = 30.0
    mode: str = "gemini"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="gemini-chat",
            provider_type="chat",
            mode=self.mode,
            default_model=self.model_name,
        )

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        normalized_model = self.model_name if self.model_name.startswith("models/") else f"models/{self.model_name}"
        try:
            response = httpx.post(
                f"{self.base_url.rstrip('/')}/{normalized_model}:generateContent",
                params={"key": self.api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": user_input}]}],
                    "generationConfig": {
                        "temperature": self.temperature,
                        "maxOutputTokens": self.max_tokens,
                    },
                },
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ChatProviderError("Gemini 请求超时。", reason="timeout") from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError("Gemini 请求失败。", reason="network_error") from exc

        if response.status_code >= 400:
            raise ChatProviderError(f"Gemini 返回 HTTP {response.status_code}。", reason="http_error", status_code=response.status_code)

        payload = response.json()
        parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        content = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
        if not content:
            raise ChatProviderError("Gemini 返回空内容。", reason="empty_content")

        return ChatCompletionResult(
            content=content,
            metadata={
                "provider_mode": self.mode,
                "base_url": self.base_url,
                "model_name": self.model_name,
                "transport": "gemini_generate_content",
            },
        )
