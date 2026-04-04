from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest
from app.schemas.ask import AskRequest, AskResponse

router = APIRouter()


def build_error_response(*, status_code: int, answer: str, trace_id: str) -> JSONResponse:
    payload = AskResponse(
        answer=answer,
        mode="ask",
        status="invalid_input" if status_code == 422 else "provider_error",
        citations=[],
        trace_id=trace_id,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse | JSONResponse:
    requested_scope = payload.knowledge_scope
    effective_scope = requested_scope
    chat_request = ChatRequest(
        mode="ask",
        user_input=payload.question,
        payload={
            "knowledge_scope_requested": requested_scope,
            "knowledge_scope_effective": effective_scope,
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
            answer="v0.1.6 当前只支持 public 公共政策问答范围。",
            trace_id=chat_request.trace_id,
        )

    try:
        result = AIRuntimeOrchestrator().run(chat_request)
    except Exception:
        return build_error_response(
            status_code=502,
            answer="当前问答服务暂不可用，请稍后重试。",
            trace_id=chat_request.trace_id,
        )

    response = AskResponse(
        answer=result.response.answer,
        mode="ask",
        status=result.status,
        citations=result.citations,
        trace_id=result.trace_id,
    )
    if result.status == "provider_error":
        return JSONResponse(status_code=502, content=response.model_dump())
    if result.status == "invalid_input":
        return JSONResponse(status_code=422, content=response.model_dump())
    return response
