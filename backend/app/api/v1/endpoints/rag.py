import logging
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_admin, require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.knowledge import get_knowledge_service
from app.knowledge.schemas import KnowledgeItemListFilters
from app.rag.kb.models import RagAnswerResult, RagEvalCase, RagEvalRun, RagHealth, RagSearchRequest, RagSearchResult, RagStats
from app.rag.schemas import (
    RagExperimentalRetrievalStrategy,
    RagGraphMode,
    RagKnowledgeScope,
    RagQueryMode,
    RagQueryParams,
    RagRetrievalResult,
)
from app.rag.service import get_rag_engine_service
from app.rag.spine import RagSpineService, get_rag_spine_service
from app.settings.service import SettingsValidationError, get_settings_service

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


class RagRebuildRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: str = "all"


class RagEvalRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kb_id: str | None = None
    mode: str = "hybrid_rerank"
    top_k: int = Field(default=5, ge=1, le=20)
    cases: list[RagEvalCase] | None = None

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
    current_user: AuthenticatedUser = Depends(require_admin),
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


@router.get("/health", response_model=RagHealth)
def rag_health(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagHealth:
    return get_rag_spine_service().health(owner_user_id=current_user.user_id)


@router.get("/stats", response_model=RagStats)
def rag_stats(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagStats:
    return get_rag_spine_service().stats(owner_user_id=current_user.user_id)


@router.get("/index/stats", response_model=RagStats)
def rag_index_stats(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagStats:
    return get_rag_spine_service().stats(owner_user_id=current_user.user_id)


@router.post("/index/rebuild")
def langchain_rag_rebuild_index(
    payload: RagRebuildRequest,
    current_user: AuthenticatedUser = Depends(require_admin),
) -> dict:
    service = get_rag_spine_service()
    # Rebuild is modeled as syncing all currently visible knowledge into the user's default KB.
    kb = service.store.sync_visible_knowledge(
        owner_user_id=current_user.user_id,
        knowledge_scope="mixed",
        allowed_knowledge_item_ids=[],
        vector_backend=service._effective_vector_backend(),
    )
    return {"scope": payload.scope, "requested_by": current_user.user_id, "kb_id": kb.kb_id, **service.stats(owner_user_id=current_user.user_id).model_dump()}


@router.post("/index/file/{file_id}")
def langchain_rag_index_file(
    file_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    items = get_knowledge_service().list_visible_items(
        owner_user_id=current_user.user_id,
        filters=KnowledgeItemListFilters(file_id=file_id, is_enabled=True, session_attachable=True),
    )
    if not items:
        raise HTTPException(status_code=404, detail="file knowledge item not found")
    service = get_rag_spine_service()
    kb = service.store.sync_visible_knowledge(
        owner_user_id=current_user.user_id,
        knowledge_scope="private_sample",
        allowed_knowledge_item_ids=[item.knowledge_item_id for item in items],
        vector_backend=service._effective_vector_backend(),
    )
    return {"file_id": file_id, "kb_id": kb.kb_id, "document_count": len(items)}


@router.post("/search", response_model=RagSearchResult)
def langchain_rag_search(
    payload: RagSearchRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagSearchResult:
    return get_rag_spine_service().search(
        owner_user_id=current_user.user_id,
        request=payload.model_copy(
            update={
                "allowed_knowledge_item_ids": _resolve_visible_knowledge_item_ids(
                    owner_user_id=current_user.user_id,
                    knowledge_scope=payload.knowledge_scope,
                    requested_ids=payload.allowed_knowledge_item_ids,
                )
            }
        ),
    )


@router.post("/answer", response_model=RagAnswerResult)
def langchain_rag_answer(
    payload: RagSearchRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagAnswerResult:
    try:
        service = _build_user_generation_rag_service(current_user=current_user, payload=payload)
        return service.answer(owner_user_id=current_user.user_id, request=_with_visible_knowledge_ids(current_user=current_user, payload=payload))
    except SettingsValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/test-qa")
def rag_test_qa(
    payload: RagSearchRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        service = _build_user_generation_rag_service(current_user=current_user, payload=payload)
        return service.test_qa(owner_user_id=current_user.user_id, request=_with_visible_knowledge_ids(current_user=current_user, payload=payload))
    except SettingsValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/eval/run", response_model=RagEvalRun)
def rag_eval_run(
    payload: RagEvalRunRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagEvalRun:
    cases = payload.cases or _load_default_eval_cases(kb_id=payload.kb_id)
    if not cases:
        raise HTTPException(status_code=422, detail="No RAG eval cases were provided or found.")
    return get_rag_spine_service().run_eval(
        owner_user_id=current_user.user_id,
        kb_id=payload.kb_id,
        cases=cases,
        mode=payload.mode,
        top_k=payload.top_k,
    )


@router.get("/eval/runs", response_model=list[RagEvalRun])
def rag_eval_runs(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[RagEvalRun]:
    return get_rag_spine_service().list_eval_runs(owner_user_id=current_user.user_id)


@router.get("/eval/runs/{run_id}", response_model=RagEvalRun)
def rag_eval_run_detail(
    run_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagEvalRun:
    try:
        return get_rag_spine_service().get_eval_run(owner_user_id=current_user.user_id, run_id=run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="RAG eval run not found") from exc


def _load_default_eval_cases(*, kb_id: str | None) -> list[RagEvalCase]:
    path = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "rag" / "gold_questions.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("cases", raw) if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        return []
    cases: list[RagEvalCase] = []
    for record in records:
        if isinstance(record, dict):
            payload = dict(record)
            if kb_id and not payload.get("expected_kb_id"):
                payload["expected_kb_id"] = kb_id
            cases.append(RagEvalCase.model_validate(payload))
    return cases


def _with_visible_knowledge_ids(*, current_user: AuthenticatedUser, payload: RagSearchRequest) -> RagSearchRequest:
    return payload.model_copy(
        update={
            "allowed_knowledge_item_ids": _resolve_visible_knowledge_item_ids(
                owner_user_id=current_user.user_id,
                knowledge_scope=payload.knowledge_scope,
                requested_ids=payload.allowed_knowledge_item_ids,
            )
        }
    )


def _build_user_generation_rag_service(*, current_user: AuthenticatedUser, payload: RagSearchRequest) -> RagSpineService:
    resolved, chat_provider = get_settings_service().build_chat_provider(
        owner_user_id=current_user.user_id,
        provider_override=payload.provider_override,
    )
    base_service = get_rag_spine_service()
    return RagSpineService(store=base_service.store, chat_provider=chat_provider, provider_ref=resolved.provider_ref)
