from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    mode: str
    user_input: str
    payload: dict[str, Any] = Field(default_factory=dict)
    trace_id: str = Field(default_factory=lambda: f"trace-{uuid4().hex[:12]}")


class ChatResponse(BaseModel):
    mode: str
    status: Literal["ok", "provider_error", "invalid_input", "stub_ready", "not_implemented", "blocked"]
    answer: str
    trace_id: str
    provider_name: str
    provider_mode: str
    model_name: str | None = None
