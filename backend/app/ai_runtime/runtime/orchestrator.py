from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.modes import list_mode_names, resolve_mode
from app.ai_runtime.providers.base import ChatCompletionResult, ChatProviderError
from app.ai_runtime.providers.factory import get_chat_provider, get_embedding_provider
from app.ai_runtime.runtime.context_builder import build_context_bundle
from app.ai_runtime.runtime.guards import (
    enforce_ask_request_constraints,
    enforce_mode_whitelist,
    enforce_tool_whitelist,
)
from app.ai_runtime.runtime.response_formatter import format_runtime_result
from app.ai_runtime.schemas.chat import ChatRequest
from app.ai_runtime.schemas.result import RuntimeResult
from app.ai_runtime.schemas.tool import ToolCall
from app.ai_runtime.tools.registry import ToolRegistry, build_default_registry


class AIRuntimeOrchestrator:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        *,
        chat_provider=None,
        embedding_provider=None,
    ) -> None:
        self.config = get_ai_runtime_config()
        self.registry = registry or build_default_registry()
        self.chat_provider = chat_provider or get_chat_provider()
        self.embedding_provider = embedding_provider or get_embedding_provider()

    def supported_modes(self) -> list[str]:
        return list_mode_names()

    def run(self, request: ChatRequest) -> RuntimeResult:
        mode = resolve_mode(request.mode)
        enforce_mode_whitelist(mode.name, self.config.allowed_modes)
        if request.mode == "ask":
            enforce_ask_request_constraints(request)

        context_bundle = build_context_bundle(request, mode)
        guard_snapshot = enforce_tool_whitelist(
            mode,
            self.registry,
            mode.default_stub_tool_sequence,
        )

        tool_calls = [
            ToolCall(
                name=tool_name,
                arguments={
                    "mode": request.mode,
                    "user_input": request.user_input,
                    "payload": request.payload,
                },
            )
            for tool_name in mode.default_stub_tool_sequence
        ]
        tool_results = [
            self.registry.invoke(
                call.name,
                arguments=call.arguments,
                context=context_bundle,
                trace_id=request.trace_id,
            )
            for call in tool_calls
        ]

        provider_descriptor = self.chat_provider.describe()
        embedding_descriptor = self.embedding_provider.describe()

        if mode.name != "ask":
            return format_runtime_result(
                request=request,
                provider_descriptor=provider_descriptor,
                embedding_descriptor=embedding_descriptor,
                guard_snapshot=guard_snapshot,
                context_bundle=context_bundle,
                provider_result=ChatCompletionResult(
                    content=f"[{mode.name}] mode skeleton is reserved for future implementation.",
                    metadata={"stub": True},
                ),
                tool_calls=tool_calls,
                tool_results=tool_results,
                status="stub_ready",
                answer=f"[{mode.name}] mode skeleton is reserved for future implementation.",
            )

        try:
            provider_result = self.chat_provider.generate_response(
                system_prompt=context_bundle["system_prompt"],
                user_input=request.user_input,
            )
            return format_runtime_result(
                request=request,
                provider_descriptor=provider_descriptor,
                embedding_descriptor=embedding_descriptor,
                guard_snapshot=guard_snapshot,
                context_bundle=context_bundle,
                provider_result=provider_result,
                tool_calls=tool_calls,
                tool_results=tool_results,
                status="ok",
                answer=provider_result.content,
            )
        except ChatProviderError as exc:
            return format_runtime_result(
                request=request,
                provider_descriptor=provider_descriptor,
                embedding_descriptor=embedding_descriptor,
                guard_snapshot=guard_snapshot,
                context_bundle=context_bundle,
                provider_result=ChatCompletionResult(
                    content="",
                    metadata={
                        "error_reason": exc.reason,
                        "error_message": str(exc),
                        "provider_status_code": exc.status_code,
                    },
                ),
                tool_calls=tool_calls,
                tool_results=tool_results,
                status="provider_error",
                answer="当前问答服务暂不可用，请稍后重试。",
            )
