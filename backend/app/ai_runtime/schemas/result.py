from typing import Any, Literal

from pydantic import BaseModel, Field

from app.ai_runtime.schemas.chat import ChatResponse
from app.ai_runtime.schemas.tool import ToolCall, ToolResult


class RuntimeResult(BaseModel):
    mode: str
    status: Literal["stub_ready", "not_implemented", "blocked"]
    trace_id: str
    context_summary: dict[str, Any] = Field(default_factory=dict)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    response: ChatResponse
    metadata: dict[str, Any] = Field(default_factory=dict)
