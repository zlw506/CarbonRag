from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


WorkflowNodeName = Literal["parse_document", "chunk_document", "upsert_vectors", "build_graph", "mark_indexed"]
WorkflowNodeStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]


class WorkflowNode(BaseModel):
    node_id: str
    name: WorkflowNodeName
    status: WorkflowNodeStatus = "pending"
    depends_on: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ExecutionCheckpoint(BaseModel):
    checkpoint_id: str = Field(default_factory=lambda: f"rag-checkpoint-{uuid4().hex[:12]}")
    workflow_run_id: str
    node_id: str
    status: WorkflowNodeStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict = Field(default_factory=dict)


class WorkflowRun(BaseModel):
    workflow_run_id: str = Field(default_factory=lambda: f"rag-workflow-{uuid4().hex[:12]}")
    knowledge_item_id: str | None = None
    status: WorkflowNodeStatus = "pending"
    nodes: list[WorkflowNode] = Field(default_factory=list)
    checkpoints: list[ExecutionCheckpoint] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


def build_default_indexing_workflow(*, knowledge_item_id: str | None = None) -> WorkflowRun:
    nodes = [
        WorkflowNode(node_id="parse", name="parse_document"),
        WorkflowNode(node_id="chunk", name="chunk_document", depends_on=["parse"]),
        WorkflowNode(node_id="vector", name="upsert_vectors", depends_on=["chunk"]),
        WorkflowNode(node_id="graph", name="build_graph", depends_on=["chunk"]),
        WorkflowNode(node_id="indexed", name="mark_indexed", depends_on=["vector", "graph"]),
    ]
    return WorkflowRun(knowledge_item_id=knowledge_item_id, nodes=nodes)
