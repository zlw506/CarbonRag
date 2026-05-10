from dataclasses import dataclass
from typing import Sequence

import httpx

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
        if not texts:
            return EmbeddingResult(vectors=[], metadata={"model_name": self.model_name, "vector_count": 0})
        if not self.api_key or self.api_key.startswith("replace-with"):
            raise RuntimeError("Embedding API key is not configured; set EMBEDDING_API_KEY.")
        if not self.model_name or self.model_name.startswith("replace-with"):
            raise RuntimeError("Embedding model is not configured; set EMBEDDING_MODEL.")
        url = f"{self.base_url.rstrip('/')}/embeddings"
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model_name, "input": list(texts)},
            )
            response.raise_for_status()
            payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise RuntimeError("Embedding API returned no data array.")
        vectors_by_index: dict[int, list[float]] = {}
        for fallback_index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            vector = item.get("embedding")
            if not isinstance(vector, list) or not vector:
                continue
            index = int(item.get("index", fallback_index))
            vectors_by_index[index] = [float(value) for value in vector]
        vectors = [vectors_by_index[index] for index in range(len(texts)) if index in vectors_by_index]
        if len(vectors) != len(texts):
            raise RuntimeError(f"Embedding API returned {len(vectors)} vectors for {len(texts)} input texts.")
        return EmbeddingResult(
            vectors=vectors,
            metadata={"model_name": self.model_name, "vector_count": len(vectors)}
        )
