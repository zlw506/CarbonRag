import logging

from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.knowledge import get_knowledge_service
from app.rag.schemas import (
    RagExperimentalRetrievalStrategy,
    RagGraphMode,
    RagKnowledgeScope,
    RagQueryMode,
    RagQueryParams,
    RagRetrievalResult,
)
from app.rag.service import get_rag_engine_service

router = APIRouter(prefix="/rag")
logger = logging.getLogger(__name__)


class RagRetrieveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    mode: RagQueryMode = "mix"
    knowledge_scope: RagKnowledgeScope = "mixed"
    top_k: int = Field(default=5, ge=1, le=20)
    chunk_top_k: int | None = Field(default=None, ge=1, le=50)
    max_total_tokens: int = Field(default=30_000, ge=1)
    enable_rerank: bool = True
    include_references: bool = True
    allowed_knowledge_item_ids: list[str] = Field(default_factory=list)
    region: str | None = None
    doc_type: str | None = None
    retrieval_strategy: RagExperimentalRetrievalStrategy | None = None
    graph_mode: RagGraphMode = "off"

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("question cannot be blank")
        return normalized

    @field_validator("allowed_knowledge_item_ids")
    @classmethod
    def normalize_allowed_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

def _resolve_visible_knowledge_item_ids(
    *,
    owner_user_id: str,
    knowledge_scope: RagKnowledgeScope,
    requested_ids: list[str],
) -> list[str]:
    if knowledge_scope == "public" or not requested_ids:
        return []

    visible_items = get_knowledge_service().list_visible_items(
        owner_user_id=owner_user_id,
        knowledge_item_ids=requested_ids,
        session_attachable=True,
        is_enabled=True,
    )
    visible_ids = {item.knowledge_item_id for item in visible_items}
    unknown_ids = [item_id for item_id in requested_ids if item_id not in visible_ids]
    if unknown_ids:
        raise HTTPException(status_code=422, detail="Selected knowledge items are not visible or attachable.")
    return [item_id for item_id in requested_ids if item_id in visible_ids]


@router.post("/retrieve", response_model=RagRetrievalResult)
def retrieve_rag_evidence(
    payload: RagRetrieveRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagRetrievalResult:
    allowed_knowledge_item_ids = _resolve_visible_knowledge_item_ids(
        owner_user_id=current_user.user_id,
        knowledge_scope=payload.knowledge_scope,
        requested_ids=payload.allowed_knowledge_item_ids,
    )
    params = RagQueryParams(
        question=payload.question,
        mode=payload.mode,
        knowledge_scope=payload.knowledge_scope,
        top_k=payload.top_k,
        chunk_top_k=payload.chunk_top_k,
        max_total_tokens=payload.max_total_tokens,
        enable_rerank=payload.enable_rerank,
        include_references=payload.include_references,
        retrieval_only=True,
        allowed_knowledge_item_ids=allowed_knowledge_item_ids,
        region=payload.region,
        doc_type=payload.doc_type,
        retrieval_strategy=payload.retrieval_strategy,
        graph_mode=payload.graph_mode,
    )
    try:
        return get_rag_engine_service().retrieve(params)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("RAG retrieval failed.", extra={"user_id": current_user.user_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": "rag_retrieval_failed",
                "error_code": "rag_retrieval_failed",
                "message": "RAG retrieval failed. Please retry later.",
            },
        ) from exc
