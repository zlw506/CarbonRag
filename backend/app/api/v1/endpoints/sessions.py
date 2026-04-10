from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest
from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.schemas.ask import AskCitation, AskRequest, AskResponse, AskSourceSummary
from app.session.schemas import CreateSessionRequest, SessionDetail, SessionSummary, UpdateSessionRequest
from app.session.service import get_session_service

router = APIRouter(prefix="/sessions")


def build_error_response(*, status_code: int, answer: str, trace_id: str, knowledge_scope: str) -> JSONResponse:
    payload = AskResponse(
        answer=answer,
        mode="ask",
        status="invalid_input" if status_code == 422 else "provider_error",
        citations=[],
        source_summary=AskSourceSummary(
            knowledge_scope=knowledge_scope,
            public_policy_count=0,
            private_sample_count=0,
            private_upload_count=0,
            total_citation_count=0,
        ),
        trace_id=trace_id,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@router.post("", response_model=SessionSummary)
def create_session(
    payload: CreateSessionRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> SessionSummary:
    return get_session_service().create_session(owner_user_id=current_user.user_id, title=payload.title)


@router.get("", response_model=list[SessionSummary])
def list_sessions(current_user: AuthenticatedUser = Depends(require_authenticated_user)) -> list[SessionSummary]:
    return get_session_service().list_sessions(owner_user_id=current_user.user_id)


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> SessionDetail:
    session = get_session_service().get_session(owner_user_id=current_user.user_id, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.patch("/{session_id}", response_model=SessionSummary)
def update_session_title(
    session_id: str,
    payload: UpdateSessionRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> SessionSummary:
    session = get_session_service().update_session_title(
        owner_user_id=current_user.user_id,
        session_id=session_id,
        title=payload.title,
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.post("/{session_id}/ask", response_model=AskResponse)
def ask_in_session(
    session_id: str,
    payload: AskRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> AskResponse | JSONResponse:
    session_service = get_session_service()
    session = session_service.get_session(owner_user_id=current_user.user_id, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    requested_scope = payload.knowledge_scope
    attached_knowledge_item_ids = session_service.list_attached_knowledge_item_ids(
        owner_user_id=current_user.user_id,
        session_id=session_id,
    )
    attached_knowledge_item_set = set(attached_knowledge_item_ids)
    filtered_knowledge_item_ids = [
        item
        for item in (payload.attached_knowledge_item_ids or payload.attached_file_ids)
        if item in attached_knowledge_item_set
    ]
    effective_knowledge_item_ids = (
        filtered_knowledge_item_ids if (payload.attached_knowledge_item_ids or payload.attached_file_ids) else attached_knowledge_item_ids
    )

    chat_request = ChatRequest(
        mode="ask",
        user_input=payload.question,
        payload={
            "session_id": session_id,
            **session_service.build_session_context(
                owner_user_id=current_user.user_id,
                session_id=session_id,
                max_turns=6,
                upcoming_user_input=payload.question,
            ),
            "knowledge_scope_requested": requested_scope,
            "knowledge_scope_effective": requested_scope,
            "top_k": payload.top_k,
            "attached_file_ids": payload.attached_file_ids,
            "attached_knowledge_item_ids": effective_knowledge_item_ids,
        },
    )

    config = get_ai_runtime_config()
    if not chat_request.user_input:
        return build_error_response(
            status_code=422,
            answer="Question cannot be empty.",
            trace_id=chat_request.trace_id,
            knowledge_scope=requested_scope,
        )
    if len(chat_request.user_input) > config.ask_max_question_length:
        return build_error_response(
            status_code=422,
            answer=f"Question cannot exceed {config.ask_max_question_length} characters.",
            trace_id=chat_request.trace_id,
            knowledge_scope=requested_scope,
        )

    try:
        result = AIRuntimeOrchestrator().run(chat_request)
    except Exception:
        source_summary = AskSourceSummary(
            knowledge_scope=requested_scope,
            public_policy_count=0,
            private_sample_count=0,
            private_upload_count=0,
            total_citation_count=0,
        )
        session_service.record_exchange(
            owner_user_id=current_user.user_id,
            session_id=session_id,
            user_content=chat_request.user_input,
            assistant_content="The ask service is temporarily unavailable. Please try again later.",
            assistant_status="provider_error",
            trace_id=chat_request.trace_id,
            citations=[],
            knowledge_scope=requested_scope,
            source_summary=source_summary,
        )
        return build_error_response(
            status_code=502,
            answer="The ask service is temporarily unavailable. Please try again later.",
            trace_id=chat_request.trace_id,
            knowledge_scope=requested_scope,
        )

    citations = [AskCitation.model_validate(citation) for citation in result.citations]
    source_summary = AskSourceSummary.model_validate(result.source_summary)
    session_service.record_exchange(
        owner_user_id=current_user.user_id,
        session_id=session_id,
        user_content=chat_request.user_input,
        assistant_content=result.response.answer,
        assistant_status=result.status,
        trace_id=result.trace_id,
        citations=citations,
        knowledge_scope=source_summary.knowledge_scope,
        source_summary=source_summary,
    )
    if result.status == "ok":
        session_service.maybe_promote_title_from_first_question(
            owner_user_id=current_user.user_id,
            session_id=session_id,
            question=chat_request.user_input,
        )

    response = AskResponse(
        answer=result.response.answer,
        mode="ask",
        status=result.status,
        citations=citations,
        source_summary=source_summary,
        trace_id=result.trace_id,
    )
    if result.status == "provider_error":
        return JSONResponse(status_code=502, content=response.model_dump())
    if result.status == "invalid_input":
        return JSONResponse(status_code=422, content=response.model_dump())
    return response
