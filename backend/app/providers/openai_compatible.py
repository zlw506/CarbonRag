from dataclasses import dataclass

import httpx

from app.providers.base import BaseProvider, ProviderDescriptor


@dataclass
class OpenAICompatibleProvider(BaseProvider):
    base_url: str
    api_key: str
    model_name: str = "gpt-5.4"
    mode: str = "openai_compatible"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(name="openai-compatible", mode=self.mode, default_model=self.model_name)

    def list_models(self) -> dict:
        response = httpx.get(
            f"{self.base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=20.0
        )
        response.raise_for_status()
        return response.json()
