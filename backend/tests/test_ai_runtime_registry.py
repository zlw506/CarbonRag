import pytest

from app.ai_runtime.tools.policy_retrieve import PolicyRetrieveTool
from app.ai_runtime.tools.registry import ToolRegistry, build_default_registry


def test_default_registry_contains_all_stub_tools() -> None:
    registry = build_default_registry()

    assert registry.list_tool_names() == [
        "carbon_calc",
        "carbon_factor_lookup",
        "enterprise_retrieve",
        "mixed_retrieve",
        "policy_retrieve",
        "report_draft",
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
