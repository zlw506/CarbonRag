from dataclasses import dataclass

from pydantic import BaseModel

from app.ai_runtime.modes.ask_mode import (
    ALLOWED_TOOLS as ASK_ALLOWED_TOOLS,
    DEFAULT_STUB_TOOL_SEQUENCE as ASK_DEFAULT_STUB_TOOL_SEQUENCE,
    MODE_NAME as ASK_MODE_NAME,
    PROMPT_POLICY as ASK_PROMPT_POLICY,
    RESPONSE_SCHEMA as ASK_RESPONSE_SCHEMA,
)
from app.ai_runtime.modes.carbon_mode import (
    ALLOWED_TOOLS as CARBON_ALLOWED_TOOLS,
    DEFAULT_STUB_TOOL_SEQUENCE as CARBON_DEFAULT_STUB_TOOL_SEQUENCE,
    MODE_NAME as CARBON_MODE_NAME,
    PROMPT_POLICY as CARBON_PROMPT_POLICY,
    RESPONSE_SCHEMA as CARBON_RESPONSE_SCHEMA,
)
from app.ai_runtime.modes.report_mode import (
    ALLOWED_TOOLS as REPORT_ALLOWED_TOOLS,
    DEFAULT_STUB_TOOL_SEQUENCE as REPORT_DEFAULT_STUB_TOOL_SEQUENCE,
    MODE_NAME as REPORT_MODE_NAME,
    PROMPT_POLICY as REPORT_PROMPT_POLICY,
    RESPONSE_SCHEMA as REPORT_RESPONSE_SCHEMA,
)


@dataclass(frozen=True)
class ModeSpec:
    name: str
    allowed_tools: tuple[str, ...]
    default_stub_tool_sequence: tuple[str, ...]
    response_schema: type[BaseModel]
    prompt_policy: str


MODE_REGISTRY = {
    ASK_MODE_NAME: ModeSpec(
        name=ASK_MODE_NAME,
        allowed_tools=ASK_ALLOWED_TOOLS,
        default_stub_tool_sequence=ASK_DEFAULT_STUB_TOOL_SEQUENCE,
        response_schema=ASK_RESPONSE_SCHEMA,
        prompt_policy=ASK_PROMPT_POLICY
    ),
    CARBON_MODE_NAME: ModeSpec(
        name=CARBON_MODE_NAME,
        allowed_tools=CARBON_ALLOWED_TOOLS,
        default_stub_tool_sequence=CARBON_DEFAULT_STUB_TOOL_SEQUENCE,
        response_schema=CARBON_RESPONSE_SCHEMA,
        prompt_policy=CARBON_PROMPT_POLICY
    ),
    REPORT_MODE_NAME: ModeSpec(
        name=REPORT_MODE_NAME,
        allowed_tools=REPORT_ALLOWED_TOOLS,
        default_stub_tool_sequence=REPORT_DEFAULT_STUB_TOOL_SEQUENCE,
        response_schema=REPORT_RESPONSE_SCHEMA,
        prompt_policy=REPORT_PROMPT_POLICY
    ),
}


def list_mode_names() -> list[str]:
    return sorted(MODE_REGISTRY)


def resolve_mode(mode_name: str) -> ModeSpec:
    try:
        return MODE_REGISTRY[mode_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported ai runtime mode: {mode_name}") from exc
