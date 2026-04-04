from app.ai_runtime.providers.base import ChatCompletionResult, ProviderDescriptor
from app.ai_runtime.runtime.guards import GuardSnapshot
from app.ai_runtime.schemas.chat import ChatRequest, ChatResponse
from app.ai_runtime.schemas.result import RuntimeResult
from app.ai_runtime.schemas.tool import ToolCall, ToolResult


def _extract_citations(tool_results: list[ToolResult]) -> list[dict]:
    citations: list[dict] = []
    for tool_result in tool_results:
        if tool_result.name != "policy_retrieve":
            continue
        hits = tool_result.output.get("hits", [])
        if not isinstance(hits, list):
            continue
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            citations.append(
                {
                    "doc_id": hit.get("doc_id"),
                    "title": hit.get("title"),
                    "source": hit.get("source"),
                    "source_url": hit.get("source_url"),
                    "snippet": hit.get("snippet"),
                    "chunk_id": hit.get("chunk_id"),
                }
            )
    return citations


def format_runtime_result(
    *,
    request: ChatRequest,
    provider_descriptor: ProviderDescriptor,
    embedding_descriptor: ProviderDescriptor,
    guard_snapshot: GuardSnapshot,
    context_bundle: dict,
    provider_result: ChatCompletionResult,
    tool_calls: list[ToolCall],
    tool_results: list[ToolResult],
    status: str,
    answer: str,
) -> RuntimeResult:
    citations = _extract_citations(tool_results)
    context_summary = {
        "payload_keys": context_bundle.get("payload_keys", []),
        "memory_reserved": not context_bundle.get("memory_slot", {}).get("implemented", False),
        "tool_count": len(tool_calls),
    }
    if request.mode == "ask":
        context_summary.update(
            {
                "knowledge_scope_requested": context_bundle.get("knowledge_scope_requested"),
                "knowledge_scope_effective": context_bundle.get("knowledge_scope_effective"),
                "single_turn_only": True,
                "grounded_by_policy": True,
                "retrieval_hit_count": len(citations),
                "citation_count": len(citations),
            }
        )
    else:
        context_summary.update(
            {
                "policy_ready": context_bundle.get("policy_context", {}).get("ready"),
                "enterprise_ready": context_bundle.get("enterprise_context", {}).get("ready"),
                "carbon_ready": context_bundle.get("carbon_context", {}).get("ready"),
                "report_ready": context_bundle.get("report_context", {}).get("ready"),
            }
        )

    response = ChatResponse(
        mode=request.mode,
        status=status,
        answer=answer,
        trace_id=request.trace_id,
        provider_name=provider_descriptor.name,
        provider_mode=provider_descriptor.mode,
        model_name=provider_descriptor.default_model,
    )

    return RuntimeResult(
        mode=request.mode,
        status=status,
        trace_id=request.trace_id,
        context_summary=context_summary,
        tool_calls=tool_calls,
        tool_results=tool_results,
        citations=citations,
        response=response,
        metadata={
            "chat_provider": provider_descriptor.name,
            "embedding_provider": embedding_descriptor.name,
            "forbidden_capabilities": list(guard_snapshot.forbidden_capabilities),
            "provider_metadata": provider_result.metadata,
        },
    )
