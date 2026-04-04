from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.modes import list_mode_names, resolve_mode
from app.ai_runtime.providers.factory import get_chat_provider, get_embedding_provider
from app.ai_runtime.runtime.context_builder import build_context_bundle
from app.ai_runtime.runtime.guards import enforce_mode_whitelist, enforce_tool_whitelist
from app.ai_runtime.runtime.response_formatter import format_runtime_result
from app.ai_runtime.schemas.chat import ChatRequest
from app.ai_runtime.schemas.result import RuntimeResult
from app.ai_runtime.schemas.tool import ToolCall
from app.ai_runtime.tools.registry import ToolRegistry, build_default_registry


class AIRuntimeOrchestrator:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.config = get_ai_runtime_config()
        self.registry = registry or build_default_registry()
        self.chat_provider = get_chat_provider()
        self.embedding_provider = get_embedding_provider()

    def supported_modes(self) -> list[str]:
        return list_mode_names()

    def run(self, request: ChatRequest) -> RuntimeResult:
        mode = resolve_mode(request.mode)
        enforce_mode_whitelist(mode.name, self.config.allowed_modes)

        context_bundle = build_context_bundle(request, mode)
        guard_snapshot = enforce_tool_whitelist(
            mode,
            self.registry,
            mode.default_stub_tool_sequence
        )

        tool_calls = [
            ToolCall(
                name=tool_name,
                arguments={
                    "mode": request.mode,
                    "user_input": request.user_input,
                    "payload": request.payload,
                }
            )
            for tool_name in mode.default_stub_tool_sequence
        ]
        tool_results = [
            self.registry.invoke(
                call.name,
                arguments=call.arguments,
                context=context_bundle,
                trace_id=request.trace_id
            )
            for call in tool_calls
        ]

        provider_result = self.chat_provider.generate_stub_response(
            mode_name=mode.name,
            user_input=request.user_input,
            tool_names=mode.default_stub_tool_sequence
        )

        return format_runtime_result(
            request=request,
            provider_descriptor=self.chat_provider.describe(),
            embedding_descriptor=self.embedding_provider.describe(),
            guard_snapshot=guard_snapshot,
            context_bundle=context_bundle,
            provider_result=provider_result,
            tool_calls=tool_calls,
            tool_results=tool_results
        )
