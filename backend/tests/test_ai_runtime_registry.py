import pytest

from app.ai_runtime.tools.policy_retrieve import PolicyRetrieveTool
from app.ai_runtime.tools.registry import ToolRegistry, build_default_registry


def test_default_registry_contains_all_stub_tools() -> None:
    registry = build_default_registry()

    assert registry.list_tool_names() == [
        "carbon_calc",
        "carbon_factor_lookup",
        "enterprise_retrieve",
        "langchain_rag_answer",
        "langchain_rag_search",
        "mixed_retrieve",
        "policy_retrieve",
        "rag_pro_answer",
        "rag_pro_search",
        "report_carbon_extract_calc",
        "report_draft",
        "session_file_search",
    ]


def test_registry_rejects_duplicate_registration() -> None:
    registry = ToolRegistry()
    registry.register(PolicyRetrieveTool())

    with pytest.raises(ValueError, match="Tool already registered"):
        registry.register(PolicyRetrieveTool())


def test_registry_raises_for_unknown_tool() -> None:
    registry = build_default_registry()

    with pytest.raises(KeyError, match="Unknown tool"):
        registry.get("missing_tool")


def test_carbon_factor_lookup_returns_real_factor_records() -> None:
    registry = build_default_registry()

    result = registry.invoke(
        "carbon_factor_lookup",
        arguments={"question": "外购电力碳因子是多少？", "top_k": 3},
        context={},
        trace_id="trace-factor",
    )

    assert result.status == "success"
    assert result.output["hit_count"] >= 1
    first_hit = result.output["hits"][0]
    assert first_hit["source_type"] == "carbon_factor"
    assert first_hit["factor_value"] > 0
    assert first_hit["factor_unit"]
    assert first_hit["factor_id"] != "electricity_grid_factor_stub"
