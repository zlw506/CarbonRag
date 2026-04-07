from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest
from app.schemas.ask import AskCitation, AskRequest, AskResponse
from app.session.schemas import CreateSessionRequest, SessionDetail, SessionSummary, UpdateSessionRequest
from app.session.service import get_session_service

router = APIRouter(prefix="/sessions")


def build_error_response(*, status_code: int, answer: str, trace_id: str) -> JSONResponse:
    payload = AskResponse(
        answer=answer,
        mode="ask",
        status="invalid_input" if status_code == 422 else "provider_error",
        citations=[],
        trace_id=trace_id,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@router.post("", response_model=SessionSummary)
def create_session(payload: CreateSessionRequest) -> SessionSummary:
    return get_session_service().create_session(title=payload.title)


@router.get("", response_model=list[SessionSummary])
def list_sessions() -> list[SessionSummary]:
    return get_session_service().list_sessions()


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: str) -> SessionDetail:
    session = get_session_service().get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在。")
    return session


@router.patch("/{session_id}", response_model=SessionSummary)
def update_session_title(session_id: str, payload: UpdateSessionRequest) -> SessionSummary:
    session = get_session_service().update_session_title(session_id, payload.title)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在。")
    return session


@router.post("/{session_id}/ask", response_model=AskResponse)
def ask_in_session(session_id: str, payload: AskRequest) -> AskResponse | JSONResponse:
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在。")

    requested_scope = payload.knowledge_scope
    chat_request = ChatRequest(
        mode="ask",
        user_input=payload.question,
        payload={
            "session_id": session_id,
            "session_context": session_service.build_session_context(session_id, max_turns=4),
            "knowledge_scope_requested": requested_scope,
            "knowledge_scope_effective": requested_scope,
            "top_k": payload.top_k,
        },
    )

    config = get_ai_runtime_config()
    if not chat_request.user_input:
        return build_error_response(
            status_code=422,
            answer="问题不能为空。",
            trace_id=chat_request.trace_id,
        )
    if len(chat_request.user_input) > config.ask_max_question_length:
        return build_error_response(
            status_code=422,
            answer=f"问题长度不能超过 {config.ask_max_question_length} 个字符。",
            trace_id=chat_request.trace_id,
        )
    if requested_scope != "public":
        return build_error_response(
            status_code=422,
            answer="v0.1.7 当前只支持 public 公共政策问答范围。",
            trace_id=chat_request.trace_id,
        )

    try:
        result = AIRuntimeOrchestrator().run(chat_request)
    except Exception:
        session_service.record_exchange(
            session_id=session_id,
            user_content=chat_request.user_input,
            assistant_content="当前问答服务暂不可用，请稍后重试。",
            assistant_status="provider_error",
            trace_id=chat_request.trace_id,
            citations=[],
        )
        return build_error_response(
            status_code=502,
            answer="当前问答服务暂不可用，请稍后重试。",
            trace_id=chat_request.trace_id,
        )

    citations = [AskCitation.model_validate(citation) for citation in result.citations]
    session_service.record_exchange(
        session_id=session_id,
        user_content=chat_request.user_input,
        assistant_content=result.response.answer,
        assistant_status=result.status,
        trace_id=result.trace_id,
        citations=citations,
    )
    if result.status == "ok":
        session_service.maybe_promote_title_from_first_question(session_id, chat_request.user_input)

    response = AskResponse(
        answer=result.response.answer,
        mode="ask",
        status=result.status,
        citations=citations,
        trace_id=result.trace_id,
    )
    if result.status == "provider_error":
        return JSONResponse(status_code=502, content=response.model_dump())
    if result.status == "invalid_input":
        return JSONResponse(status_code=422, content=response.model_dump())
    return response
