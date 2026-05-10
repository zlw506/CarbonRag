from __future__ import annotations

import hashlib
import math
from typing import Iterable

from app.ai_runtime.providers.factory import get_embedding_provider

try:  # pragma: no cover - exercised when langchain is installed
    from langchain_core.embeddings import Embeddings
except Exception:  # noqa: BLE001
    class Embeddings:  # type: ignore[no-redef]
        pass


class CarbonRagEmbeddings(Embeddings):
    """LangChain embedding adapter over CarbonRag's configured embedding provider."""

    def __init__(self, *, dimensions: int = 384) -> None:
        self.dimensions = dimensions
        self.provider = get_embedding_provider()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            result = self.provider.embed_stub(texts)
            if len(result.vectors) == len(texts) and all(result.vectors):
                return result.vectors
        except Exception:  # noqa: BLE001
            pass
        return [_hash_embedding(text, dimensions=self.dimensions) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def _hash_embedding(text: str, *, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    tokens = list(_tokenize_for_hash(text))
    if not tokens:
        tokens = [text or "empty"]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8", errors="ignore")).digest()
        for offset in range(0, min(len(digest), 32), 2):
            index = int.from_bytes(digest[offset:offset + 2], "big") % dimensions
            vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _tokenize_for_hash(text: str) -> Iterable[str]:
    normalized = text.strip().lower()
    if not normalized:
        return []
    return normalized.replace("\n", " ").split()
