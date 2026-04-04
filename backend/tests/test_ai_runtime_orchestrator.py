from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest


def test_orchestrator_returns_runtime_result_for_stub_request() -> None:
    orchestrator = AIRuntimeOrchestrator()
    request = ChatRequest(
        mode="ask",
        user_input="请给我一个后续将接入政策检索的占位回答。",
        payload={"knowledge_scope": "public"},
    )

    result = orchestrator.run(request)

    assert result.status == "stub_ready"
    assert result.mode == "ask"
    assert result.trace_id == request.trace_id
    assert result.context_summary["policy_ready"] is True
    assert result.context_summary["memory_reserved"] is True
    assert [tool.name for tool in result.tool_calls] == [
        "policy_retrieve",
        "enterprise_retrieve",
    ]
    assert [tool.name for tool in result.tool_results] == [
        "policy_retrieve",
        "enterprise_retrieve",
    ]
    assert result.response.mode == "ask"
    assert result.response.status == "stub_ready"
    assert result.response.provider_mode == "openai_compatible"
    assert "forbidden_capabilities" in result.metadata
