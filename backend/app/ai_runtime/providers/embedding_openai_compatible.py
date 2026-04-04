from dataclasses import dataclass
from typing import Sequence

from app.ai_runtime.providers.base import BaseEmbeddingProvider, EmbeddingResult, ProviderDescriptor


@dataclass
class OpenAICompatibleEmbeddingProvider(BaseEmbeddingProvider):
    base_url: str
    api_key: str
    model_name: str
    mode: str = "openai_compatible"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="openai-compatible-embedding",
            provider_type="embedding",
            mode=self.mode,
            default_model=self.model_name
        )

    def embed_stub(self, texts: Sequence[str]) -> EmbeddingResult:
        vectors = [
            [float(index), float(len(text)), 1.0]
            for index, text in enumerate(texts)
        ]
        return EmbeddingResult(
            vectors=vectors,
            metadata={"model_name": self.model_name, "vector_count": len(vectors)}
        )
