from __future__ import annotations

from pydantic import BaseModel, Field

from app.rag.contracts import RetrievalStrategyName
from app.rag.schemas import RagKnowledgeScope, RagQueryMode


class RetrievalStrategyPlan(BaseModel):
    name: RetrievalStrategyName
    requested_mode: RagQueryMode
    knowledge_scope: RagKnowledgeScope
    planned_layers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def plan_retrieval_strategy(*, mode: RagQueryMode, knowledge_scope: RagKnowledgeScope) -> RetrievalStrategyPlan:
    if mode == "naive":
        return RetrievalStrategyPlan(
            name="dense_only",
            requested_mode=mode,
            knowledge_scope=knowledge_scope,
            planned_layers=["vector", "bm25_fallback"],
            notes=["vector-first when configured; fallback-safe"],
        )
    return RetrievalStrategyPlan(
        name="bm25_dense_hybrid",
        requested_mode=mode,
        knowledge_scope=knowledge_scope,
        planned_layers=["vector", "graph", "bm25_fallback", "rerank"],
        notes=["graph layer may be unavailable in V1.3.x"],
    )


def build_retrieval_path(
    *,
    retrieval_layer: str,
    vector_status: str,
    graph_status: str,
    rerank_status: str,
) -> list[str]:
    path: list[str] = []
    if vector_status == "queried":
        path.append("vector")
    elif vector_status in {"disabled", "unavailable", "error"}:
        path.append(f"vector:{vector_status}")
    if graph_status not in {"skipped"}:
        path.append(f"graph:{graph_status}")
    path.append(retrieval_layer)
    if rerank_status in {"applied", "skipped", "error"}:
        path.append(f"rerank:{rerank_status}")
    elif rerank_status == "disabled":
        path.append("rerank:disabled")
    return path
