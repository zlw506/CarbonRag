from app.ai_runtime.modes import resolve_mode
from app.ai_runtime.schemas.result import RuntimeResult


def test_ask_mode_contract() -> None:
    mode = resolve_mode("ask")

    assert mode.allowed_tools == ()
    assert mode.default_stub_tool_sequence == ()
    assert mode.response_schema is RuntimeResult


def test_carbon_mode_contract() -> None:
    mode = resolve_mode("carbon")

    assert mode.allowed_tools == (
        "enterprise_retrieve",
        "carbon_factor_lookup",
        "carbon_calc",
    )
    assert mode.default_stub_tool_sequence == (
        "enterprise_retrieve",
        "carbon_factor_lookup",
        "carbon_calc",
    )
    assert mode.response_schema is RuntimeResult


def test_report_mode_contract() -> None:
    mode = resolve_mode("report")

    assert mode.allowed_tools == (
        "policy_retrieve",
        "enterprise_retrieve",
        "report_draft",
    )
    assert mode.default_stub_tool_sequence == (
        "policy_retrieve",
        "enterprise_retrieve",
        "report_draft",
    )
    assert mode.response_schema is RuntimeResult
