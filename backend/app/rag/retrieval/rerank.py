from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.rag.kb.models import RagHit


class BgeReranker:
    """RAG-Pro style BGE reranker. Fails visibly instead of pretending success."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._initialized = False
        self._error: str | None = None

    def rerank(self, *, query: str, hits: list[RagHit], top_k: int) -> tuple[list[RagHit], bool, str | None]:
        if not hits:
            return [], False, "no_hits"
        if not get_settings().rag_rerank_enabled:
            return hits[:top_k], False, "rerank_disabled"
        if not self._ensure_model():
            return hits[:top_k], False, self._error or "bge_reranker_unavailable"
        passages = [hit.snippet for hit in hits]
        try:
            scores = self._model.compute_score([[query, passage] for passage in passages], normalize=True)
        except Exception as exc:  # noqa: BLE001
            return hits[:top_k], False, f"bge_reranker_failed: {exc}"
        if isinstance(scores, (float, int)):
            scores = [float(scores)]
        reranked: list[RagHit] = []
        for index, hit in enumerate(hits):
            score = float(scores[index]) if index < len(scores) else 0.0
            reranked.append(hit.model_copy(update={"rerank_score": score}))
        reranked.sort(key=lambda item: item.rerank_score or 0.0, reverse=True)
        return reranked[:top_k], True, None

    def _ensure_model(self) -> bool:
        if self._initialized:
            return self._model is not None
        self._initialized = True
        settings = get_settings()
        if settings.rag_rerank_provider.strip().lower() not in {"bge_reranker", "bge-reranker", "cross_encoder"}:
            self._error = f"unsupported_rerank_provider:{settings.rag_rerank_provider}"
            return False
        if settings.rag_hf_endpoint and not os.environ.get("HF_ENDPOINT"):
            os.environ["HF_ENDPOINT"] = settings.rag_hf_endpoint
        os.environ.setdefault("HF_HOME", str(Path(settings.rag_model_cache_dir).parent / "hf-cache"))
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(Path(settings.rag_model_cache_dir).parent / "hf-cache" / "hub"))
        try:
            import builtins
            from typing import Optional

            if not hasattr(builtins, "Optional"):
                builtins.Optional = Optional
            from FlagEmbedding import FlagReranker
        except Exception as exc:  # noqa: BLE001
            self._error = f"FlagEmbedding is not installed; real rerank unavailable: {exc}"
            return False
        local_path = Path(settings.rag_model_cache_dir) / "BAAI" / "bge-reranker-v2-m3"
        if not _looks_like_model_dir(local_path) and not settings.rag_model_auto_download:
            self._error = (
                "BGE reranker local model is missing and auto-download is disabled; "
                f"set RAG_MODEL_AUTO_DOWNLOAD=true for smoke download, or pre-download to {local_path}"
            )
            return False
        model_path = str(local_path) if _looks_like_model_dir(local_path) else settings.rag_rerank_model
        try:
            self._model = FlagReranker(model_path, use_fp16=settings.rag_embedding_device != "cpu")
            return True
        except Exception as exc:  # noqa: BLE001
            self._error = f"Failed to load reranker '{model_path}': {exc}"
            return False


def _looks_like_model_dir(path: Path) -> bool:
    if not path.exists():
        return False
    return any(path.glob("*.bin")) or any(path.glob("*.safetensors")) or (path / "config.json").exists()
