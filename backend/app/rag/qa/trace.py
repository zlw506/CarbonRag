from __future__ import annotations

from app.rag.kb.models import RagTrace


def degraded_trace(*, reason: str, vector_backend: str = "memory", kb_id: str | None = None) -> RagTrace:
    return RagTrace(
        vector_backend=vector_backend,
        degraded=True,
        kb_id=kb_id,
        warnings=[reason],
    )

