from dataclasses import dataclass

from app.providers.base import BaseProvider, ProviderDescriptor


@dataclass
class CloudLLMStubProvider(BaseProvider):
    mode: str = "cloud_api_stub"
    model_name: str = "gpt-5.4"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(name="cloud-llm-stub", mode=self.mode, default_model=self.model_name)
