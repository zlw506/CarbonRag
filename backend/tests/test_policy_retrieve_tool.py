from app.ai_runtime.tools.policy_retrieve import PolicyRetrieveTool
from app.ai_runtime.tools.registry import build_default_registry


def test_policy_retrieve_tool_returns_retrieval_hits() -> None:
    tool = PolicyRetrieveTool()

    result = tool.invoke(
        arguments={
            "question": "什么是双碳目标？",
            "top_k": 3,
            "knowledge_scope": "public",
            "payload": {
                "knowledge_scope_effective": "public",
                "top_k": 3,
            },
        },
        context={"mode": "ask"},
        trace_id="trace-test-policy-tool",
    )

    assert result.name == "policy_retrieve"
    assert result.status == "success"
    assert result.output["hits"]
    assert result.metadata["hit_count"] >= 1
    first_hit = result.output["hits"][0]
    assert first_hit["doc_id"].startswith("policy_")
    assert first_hit["source"]
    assert first_hit["chunk_id"].startswith(first_hit["doc_id"])


def test_policy_retrieve_tool_is_registered_in_default_registry() -> None:
    registry = build_default_registry()

    tool = registry.get("policy_retrieve")

    assert tool.definition.name == "policy_retrieve"
    assert registry.list_tool_names()[0] == "carbon_calc"
