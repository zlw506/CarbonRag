from dataclasses import dataclass
from typing import Sequence

from app.ai_runtime.providers.base import BaseChatProvider, ChatCompletionResult, ProviderDescriptor


@dataclass
class OpenAICompatibleChatProvider(BaseChatProvider):
    base_url: str
    api_key: str
    model_name: str = "gpt-5.4"
    temperature: float = 0.2
    max_tokens: int = 4096
    mode: str = "openai_compatible"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="openai-compatible-chat",
            provider_type="chat",
            mode=self.mode,
            default_model=self.model_name
        )

    def generate_stub_response(
        self,
        *,
        mode_name: str,
        user_input: str,
        tool_names: Sequence[str]
    ) -> ChatCompletionResult:
        planned_tools = ", ".join(tool_names) if tool_names else "no tools"
        preview = user_input.strip()[:120] or "empty input"

        return ChatCompletionResult(
            content=(
                f"[{mode_name}] AI Runtime skeleton is ready. "
                f"Planned stub tools: {planned_tools}. "
                f"User input preview: {preview}."
            ),
            metadata={
                "provider_mode": self.mode,
                "base_url": self.base_url,
                "model_name": self.model_name
            }
        )
