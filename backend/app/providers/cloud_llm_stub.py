from dataclasses import dataclass

from app.providers.base import BaseProvider, ProviderDescriptor


@dataclass
class CloudLLMStubProvider(BaseProvider):
    mode: str = "cloud_api_stub"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(name="cloud-llm-stub", mode=self.mode)
