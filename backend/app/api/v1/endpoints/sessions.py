import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest
from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.schemas.ask import AskCitation, AskRequest, AskResponse, AskSourceSummary, MessageStatus
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


def build_chat_request(
    *,
    session_id: str,
    payload: AskRequest,
    current_user: AuthenticatedUser,
) -> tuple[ChatRequest, list[str]]:
    session_service = get_session_service()
    attached_knowledge_item_ids = session_service.list_attached_knowledge_item_ids(
        owner_user_id=current_user.user_id,
        session_id=session_id,
    )
    attached_knowledge_item_set = set(attached_knowledge_item_ids)
    requested_ids = payload.attached_knowledge_item_ids or payload.attached_file_ids
    filtered_knowledge_item_ids = [item for item in requested_ids if item in attached_knowledge_item_set]
    effective_knowledge_item_ids = filtered_knowledge_item_ids if requested_ids else attached_knowledge_item_ids

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
            "knowledge_scope_requested": payload.knowledge_scope,
            "knowledge_scope_effective": payload.knowledge_scope,
            "top_k": payload.top_k,
            "attached_file_ids": payload.attached_file_ids,
            "attached_knowledge_item_ids": effective_knowledge_item_ids,
        },
    )
    return chat_request, effective_knowledge_item_ids


def validate_chat_request(chat_request: ChatRequest, *, knowledge_scope: str) -> JSONResponse | None:
    config = get_ai_runtime_config()
    if not chat_request.user_input:
        return build_error_response(
            status_code=422,
            answer="问题不能为空。",
            trace_id=chat_request.trace_id,
            knowledge_scope=knowledge_scope,
        )
    if len(chat_request.user_input) > config.ask_max_question_length:
        return build_error_response(
            status_code=422,
            answer=f"问题长度不能超过 {config.ask_max_question_length} 个字符。",
            trace_id=chat_request.trace_id,
            knowledge_scope=knowledge_scope,
        )
    return None


def empty_source_summary(knowledge_scope: str) -> AskSourceSummary:
    return AskSourceSummary(
        knowledge_scope=knowledge_scope,
        public_policy_count=0,
        private_sample_count=0,
        private_upload_count=0,
        total_citation_count=0,
    )


def build_sse_event(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def resolve_final_message_status(result_status: str) -> MessageStatus:
    if result_status == "ok":
        return "done"
    if result_status == "invalid_input":
        return "invalid_input"
    return "provider_error"


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
    chat_request, _ = build_chat_request(session_id=session_id, payload=payload, current_user=current_user)
    validation_error = validate_chat_request(chat_request, knowledge_scope=requested_scope)
    if validation_error is not None:
        return validation_error

    try:
        result = AIRuntimeOrchestrator().run(chat_request)
    except Exception:
        source_summary = empty_source_summary(requested_scope)
        session_service.record_exchange(
            owner_user_id=current_user.user_id,
            session_id=session_id,
            user_content=chat_request.user_input,
            assistant_content="当前问答服务暂不可用，请稍后重试。",
            assistant_status="provider_error",
            trace_id=chat_request.trace_id,
            citations=[],
            knowledge_scope=requested_scope,
            source_summary=source_summary,
        )
        return build_error_response(
            status_code=502,
            answer="当前问答服务暂不可用，请稍后重试。",
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
        assistant_status=resolve_final_message_status(result.status),
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


@router.post("/{session_id}/ask/stream", response_model=None)
def ask_in_session_stream(
    session_id: str,
    payload: AskRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> StreamingResponse | JSONResponse:
    session_service = get_session_service()
    session = session_service.get_session(owner_user_id=current_user.user_id, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    requested_scope = payload.knowledge_scope
    chat_request, _ = build_chat_request(session_id=session_id, payload=payload, current_user=current_user)
    validation_error = validate_chat_request(chat_request, knowledge_scope=requested_scope)
    if validation_error is not None:
        return validation_error

    user_message, assistant_placeholder = session_service.begin_exchange(
        owner_user_id=current_user.user_id,
        session_id=session_id,
        user_content=chat_request.user_input,
    )

    def event_stream():
        yield build_sse_event(
            "message_start",
            {
                "trace_id": chat_request.trace_id,
                "user_message_id": user_message.message_id,
                "assistant_message_id": assistant_placeholder.message_id,
            },
        )
        yield build_sse_event(
            "status",
            {
                "status": "pending",
                "trace_id": chat_request.trace_id,
                "user_message_id": user_message.message_id,
                "assistant_message_id": assistant_placeholder.message_id,
            },
        )
        yield build_sse_event(
            "thinking_delta",
            {
                "delta": "正在梳理上下文。",
                "synthetic": True,
                "trace_id": chat_request.trace_id,
                "user_message_id": user_message.message_id,
                "assistant_message_id": assistant_placeholder.message_id,
            },
        )

        try:
            stream_handle = AIRuntimeOrchestrator().run_stream(chat_request)
            for event in stream_handle.events:
                if event.kind not in {"status", "thinking_delta", "answer_delta"}:
                    continue
                payload_data = {
                    **event.data,
                    "trace_id": chat_request.trace_id,
                    "user_message_id": user_message.message_id,
                    "assistant_message_id": assistant_placeholder.message_id,
                }
                yield build_sse_event(event.kind, payload_data)

            result = stream_handle.state.runtime_result
        except Exception:
            result = None

        if result is None:
            result_status = "provider_error"
            answer = "当前问答服务暂不可用，请稍后重试。"
            citations: list[AskCitation] = []
            source_summary = empty_source_summary(requested_scope)
        else:
            result_status = result.status
            answer = result.response.answer
            citations = [AskCitation.model_validate(item) for item in result.citations]
            source_summary = AskSourceSummary.model_validate(result.source_summary)

        finalized_message = session_service.finalize_exchange(
            owner_user_id=current_user.user_id,
            session_id=session_id,
            assistant_message_id=assistant_placeholder.message_id,
            assistant_content=answer,
            assistant_status=resolve_final_message_status(result_status),
            trace_id=chat_request.trace_id,
            citations=citations,
            knowledge_scope=source_summary.knowledge_scope,
            source_summary=source_summary,
        )
        if result_status == "ok":
            session_service.maybe_promote_title_from_first_question(
                owner_user_id=current_user.user_id,
                session_id=session_id,
                question=chat_request.user_input,
            )

        refreshed_session = session_service.get_session(owner_user_id=current_user.user_id, session_id=session_id)
        memory_state = refreshed_session.memory_state.model_dump(mode="json") if refreshed_session and refreshed_session.memory_state else None
        context_source = {
            "recent_message_count": result.context_summary.get("session_message_count", 0) if result is not None else 0,
            "summary_present": result.context_summary.get("summary_present", False) if result is not None else False,
            "citation_count": len(citations),
        }
        metadata_payload = {
            "answer": answer,
            "status": result_status,
            "citations": [citation.model_dump() for citation in citations],
            "source_summary": source_summary.model_dump(),
            "trace_id": chat_request.trace_id,
            "user_message_id": user_message.message_id,
            "assistant_message_id": assistant_placeholder.message_id,
            "message_id": finalized_message.message_id if finalized_message is not None else assistant_placeholder.message_id,
            "memory_state": memory_state,
            "context_source": context_source,
        }
        yield build_sse_event("metadata", metadata_payload)

        if result_status == "ok":
            yield build_sse_event(
                "status",
                {
                    "status": "done",
                    "trace_id": chat_request.trace_id,
                    "user_message_id": user_message.message_id,
                    "assistant_message_id": assistant_placeholder.message_id,
                },
            )
            yield build_sse_event("done", metadata_payload)
            return

        yield build_sse_event(
            "status",
            {
                "status": "error",
                "trace_id": chat_request.trace_id,
                "user_message_id": user_message.message_id,
                "assistant_message_id": assistant_placeholder.message_id,
            },
        )
        yield build_sse_event(
            "error",
            {
                **metadata_payload,
                "message": answer,
            },
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
