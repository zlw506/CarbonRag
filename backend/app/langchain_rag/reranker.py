from __future__ import annotations

from app.langchain_rag.config import LangChainRagConfig
from app.langchain_rag.schemas import LangChainRagHit


class CrossEncoderReranker:
    def __init__(self, *, config: LangChainRagConfig) -> None:
        self.config = config
        self._model = None
        self._reason: str | None = None

    @property
    def reason(self) -> str | None:
        return self._reason

    def rerank(self, *, query: str, hits: list[LangChainRagHit], top_k: int) -> tuple[list[LangChainRagHit], bool]:
        if not self.config.rerank_enabled:
            self._reason = "rerank_disabled"
            return hits[:top_k], False
        if not hits:
            self._reason = "no_hits"
            return hits, False
        model = self._get_model()
        if model is None:
            return hits[:top_k], False
        try:
            pairs = [(query, hit.snippet) for hit in hits]
            scores = model.predict(pairs, batch_size=1)
            ranked = []
            for hit, score in zip(hits, scores):
                score_value = float(score)
                ranked.append((score_value, hit.model_copy(update={"rerank_score": score_value, "score": score_value})))
            ranked.sort(key=lambda item: item[0], reverse=True)
            return [hit for _, hit in ranked[:top_k]], True
        except Exception as exc:  # noqa: BLE001
            self._reason = f"{type(exc).__name__}: {exc}"
            return hits[:top_k], False

    def _get_model(self):
        if self._model is not None:
            return self._model
        try:  # pragma: no cover - depends on optional model package/runtime
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.config.rerank_model)
            self._reason = None
            return self._model
        except Exception as exc:  # noqa: BLE001
            self._reason = f"{type(exc).__name__}: {exc}"
            return None
