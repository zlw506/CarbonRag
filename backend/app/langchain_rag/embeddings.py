from __future__ import annotations

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
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("real embedding provider is unavailable; hash embedding fallback is disabled") from exc
        raise RuntimeError("real embedding provider returned empty vectors; hash embedding fallback is disabled")

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
