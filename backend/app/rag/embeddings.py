from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

from app.core.config import get_settings, resolve_repo_path


class RagEmbeddingUnavailable(RuntimeError):
    """Raised when the configured real embedding runtime is unavailable."""


@dataclass(slots=True)
class RagEmbeddings:
    dense: list[list[float]]
    sparse: list[dict[str, float]]
    model_name: str
    provider: str


def embed_documents(texts: list[str]) -> RagEmbeddings:
    return get_rag_embedder().embed_documents(texts)


def embed_query(text: str) -> tuple[list[float], dict[str, float]]:
    output = get_rag_embedder().embed_query(text)
    return output.dense[0], output.sparse[0] if output.sparse else {}


@lru_cache(maxsize=2)
def get_rag_embedder() -> "BgeM3Embedder | OpenAICompatibleRagEmbedder":
    settings = get_settings()
    provider = settings.rag_embedding_provider.strip().lower()
    if provider in {"openai_compatible", "openai-compatible", "api", "cloud_api"}:
        return OpenAICompatibleRagEmbedder(
            base_url=settings.embedding_api_base_url,
            api_key=settings.embedding_api_key,
            model_name=settings.embedding_model,
        )
        return BgeM3Embedder(
            model_name=settings.rag_embedding_model,
            provider=provider,
            device=settings.rag_embedding_device,
            cache_dir=resolve_repo_path(settings.rag_model_cache_dir),
            hf_endpoint=settings.rag_hf_endpoint,
            auto_download=settings.rag_model_auto_download,
        )


class OpenAICompatibleRagEmbedder:
    """Dense embedding adapter for OpenAI-compatible cloud embedding APIs.

    This is the safe default for collaborative machines: it avoids silently
    downloading multi-GB local models to the system drive. Sparse scores still
    come from the RAG spine BM25 path, so dense-only API embeddings are enough
    for hybrid retrieval.
    """

    def __init__(self, *, base_url: str, api_key: str, model_name: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.provider = "openai_compatible"

    def embed_documents(self, texts: list[str]) -> RagEmbeddings:
        if not texts:
            return RagEmbeddings(dense=[], sparse=[], model_name=self.model_name, provider=self.provider)
        if not self.api_key or self.api_key.startswith("replace-with"):
            raise RagEmbeddingUnavailable("Embedding API key is not configured; set EMBEDDING_API_KEY or use local BGE.")
        if not self.model_name or self.model_name.startswith("replace-with"):
            raise RagEmbeddingUnavailable("Embedding model is not configured; set EMBEDDING_MODEL or use local BGE.")
        url = f"{self.base_url.rstrip('/')}/embeddings"
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self.model_name, "input": texts},
                )
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # noqa: BLE001
            raise RagEmbeddingUnavailable(f"Embedding API unavailable: {exc}") from exc
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise RagEmbeddingUnavailable("Embedding API returned no data array.")
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
            raise RagEmbeddingUnavailable(
                f"Embedding API returned {len(vectors)} vectors for {len(texts)} input texts."
            )
        return RagEmbeddings(dense=vectors, sparse=[{} for _ in vectors], model_name=self.model_name, provider=self.provider)

    def embed_query(self, text: str) -> RagEmbeddings:
        result = self.embed_documents([text])
        if not result.dense:
            raise RagEmbeddingUnavailable("Embedding API returned no query embedding.")
        return result


class BgeM3Embedder:
    """RAG-Pro style BGE-M3 wrapper for dense + sparse embeddings."""

    def __init__(
        self,
        *,
        model_name: str,
        provider: str,
        device: str,
        cache_dir: Path,
        hf_endpoint: str | None,
        auto_download: bool,
    ) -> None:
        self.model_name = model_name or "BAAI/bge-m3"
        self.provider = provider or "bge_m3"
        self.device = device or "cpu"
        self.cache_dir = cache_dir
        self.hf_endpoint = hf_endpoint
        self.auto_download = auto_download
        self._model: Any | None = None

    def embed_documents(self, texts: list[str]) -> RagEmbeddings:
        if not texts:
            return RagEmbeddings(dense=[], sparse=[], model_name=self.model_name, provider=self.provider)
        output = self._model_instance().encode(
            texts,
            batch_size=16,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )
        return RagEmbeddings(
            dense=[_to_float_list(item) for item in output.get("dense_vecs", [])],
            sparse=[_normalize_sparse_weights(item) for item in output.get("lexical_weights", [])],
            model_name=self.model_name,
            provider=self.provider,
        )

    def embed_query(self, text: str) -> RagEmbeddings:
        result = self.embed_documents([text])
        if not result.dense:
            raise RagEmbeddingUnavailable("BGE-M3 returned no query embedding.")
        return result

    def _model_instance(self):
        if self._model is not None:
            return self._model
        if self.provider.strip().lower() not in {"bge_m3", "bge-m3", "bge"}:
            raise RagEmbeddingUnavailable(f"Unsupported RAG embedding provider: {self.provider}")
        try:
            import builtins
            from typing import Optional

            # FlagEmbedding 1.2.11 references Optional during import without
            # importing it in one trainer module under newer dependency sets.
            if not hasattr(builtins, "Optional"):
                builtins.Optional = Optional
            from FlagEmbedding import BGEM3FlagModel
        except Exception as exc:  # noqa: BLE001
            raise RagEmbeddingUnavailable(f"FlagEmbedding runtime unavailable: {exc}") from exc

        local_path = self.cache_dir / "BAAI" / "bge-m3"
        model_path = str(local_path) if _looks_like_model_dir(local_path) else self._download_model(local_path)
        try:
            self._model = BGEM3FlagModel(model_path, use_fp16=self.device != "cpu")
        except Exception as exc:  # noqa: BLE001
            raise RagEmbeddingUnavailable(f"Failed to load BGE-M3 model '{model_path}': {exc}") from exc
        return self._model

    def _download_model(self, local_path: Path) -> str:
        if not self.auto_download:
            raise RagEmbeddingUnavailable(
                "BGE-M3 local model is missing and auto-download is disabled. "
                f"Set RAG_MODEL_AUTO_DOWNLOAD=true for a one-time smoke download, or pre-download to {local_path}."
            )
        if self.hf_endpoint and not os.environ.get("HF_ENDPOINT"):
            os.environ["HF_ENDPOINT"] = self.hf_endpoint
        os.environ.setdefault("HF_HOME", str(self.cache_dir.parent / "hf-cache"))
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(self.cache_dir.parent / "hf-cache" / "hub"))
        try:
            from huggingface_hub import snapshot_download
        except Exception as exc:  # noqa: BLE001
            raise RagEmbeddingUnavailable(f"huggingface_hub is unavailable for BGE-M3 download: {exc}") from exc
        try:
            return snapshot_download(
                repo_id=self.model_name,
                local_dir=str(local_path),
                ignore_patterns=["imgs/*", "*.onnx", "*.onnx_data", "onnx/*"],
            )
        except Exception as exc:  # noqa: BLE001
            raise RagEmbeddingUnavailable(f"Failed to download BGE-M3 model '{self.model_name}': {exc}") from exc


def _looks_like_model_dir(path: Path) -> bool:
    if not path.exists():
        return False
    return any(path.glob("*.bin")) or any(path.glob("*.safetensors")) or (path / "config.json").exists()


def _to_float_list(value: Any) -> list[float]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    return [float(item) for item in value]


def _normalize_sparse_weights(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    return {str(key): float(weight) for key, weight in value.items()}
