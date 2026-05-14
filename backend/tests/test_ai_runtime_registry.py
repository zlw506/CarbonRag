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
        "report_file_generate",
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
    assert result.output["skill"]["name"] == "carbon-factor-library"
    assert result.output["skill"]["index_available"] is True
    assert result.output["registry"]["record_count"] > 100
    assert result.output["registry"]["unique_activity_count"] > 50
    assert result.output["hit_count"] >= 1
    first_hit = result.output["hits"][0]
    assert first_hit["source_type"] == "carbon_factor"
    assert first_hit["factor_value"] > 0
    assert first_hit["factor_unit"]
    assert first_hit["factor_id"] != "electricity_grid_factor_stub"


def test_carbon_factor_lookup_diversifies_multi_source_queries() -> None:
    registry = build_default_registry()

    result = registry.invoke(
        "carbon_factor_lookup",
        arguments={"question": "外购电力、天然气、柴油、汽油、外购蒸汽分别用什么碳因子？", "top_k": 8},
        context={},
        trace_id="trace-factor-multi",
    )

    activity_names = {hit["activity_name"] for hit in result.output["hits"]}

    assert result.output["requested_activity_keys"] == ["electricity", "natural_gas", "diesel", "gasoline", "steam"]
    assert {"electricity", "natural_gas", "diesel", "gasoline", "steam"}.issubset(
        set(result.output["returned_activity_keys"])
    )
    assert "electricity" in activity_names
    assert "natural_gas" in activity_names or "天然气" in activity_names
    assert "diesel" in activity_names or "柴油" in activity_names
    assert "gasoline" in activity_names or "汽油" in activity_names
    assert any("蒸汽" in name for name in activity_names)


def test_carbon_factor_lookup_does_not_return_unrelated_electricity_for_refrigerant_query() -> None:
    registry = build_default_registry()

    result = registry.invoke(
        "carbon_factor_lookup",
        arguments={"question": "R410A 和 R134a 制冷剂碳因子是多少？", "top_k": 5},
        context={},
        trace_id="trace-factor-refrigerant",
    )

    assert result.output["hits"] == []
    assert result.output["warnings"]
    assert result.output["requested_activity_keys"] == ["refrigerant"]
    assert result.output["missing_requested_activity_keys"] == ["refrigerant"]


def test_carbon_factor_lookup_reports_registry_size_for_generic_count_question() -> None:
    registry = build_default_registry()

    result = registry.invoke(
        "carbon_factor_lookup",
        arguments={"question": "你那里一共可以看到多少碳因子？", "top_k": 5},
        context={},
        trace_id="trace-factor-count",
    )

    assert result.output["registry"]["record_count"] == 366
    assert result.output["registry"]["unique_activity_count"] == 315
    assert result.output["hit_count"] == 5
