from app.ai_runtime.providers.base import ChatCompletionResult, ProviderDescriptor
from app.ai_runtime.runtime.guards import GuardSnapshot
from app.ai_runtime.schemas.chat import ChatRequest, ChatResponse
from app.ai_runtime.schemas.result import RuntimeResult
from app.ai_runtime.schemas.tool import ToolCall, ToolResult


def format_runtime_result(
    *,
    request: ChatRequest,
    provider_descriptor: ProviderDescriptor,
    embedding_descriptor: ProviderDescriptor,
    guard_snapshot: GuardSnapshot,
    context_bundle: dict,
    provider_result: ChatCompletionResult,
    tool_calls: list[ToolCall],
    tool_results: list[ToolResult]
) -> RuntimeResult:
    response = ChatResponse(
        mode=request.mode,
        status="stub_ready",
        answer=provider_result.content,
        trace_id=request.trace_id,
        provider_name=provider_descriptor.name,
        provider_mode=provider_descriptor.mode,
        model_name=provider_descriptor.default_model
    )

    return RuntimeResult(
        mode=request.mode,
        status="stub_ready",
        trace_id=request.trace_id,
        context_summary={
            "policy_ready": context_bundle["policy_context"]["ready"],
            "enterprise_ready": context_bundle["enterprise_context"]["ready"],
            "carbon_ready": context_bundle["carbon_context"]["ready"],
            "report_ready": context_bundle["report_context"]["ready"],
            "memory_reserved": not context_bundle["memory_slot"]["implemented"],
            "payload_keys": context_bundle["payload_keys"],
        },
        tool_calls=tool_calls,
        tool_results=tool_results,
        response=response,
        metadata={
            "chat_provider": provider_descriptor.name,
            "embedding_provider": embedding_descriptor.name,
            "forbidden_capabilities": list(guard_snapshot.forbidden_capabilities),
            "provider_stub_metadata": provider_result.metadata,
        }
    )
