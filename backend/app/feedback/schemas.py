from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


FeedbackTargetType = Literal["ask", "calc_carbon"]
FeedbackRating = Literal["up", "down"]


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: FeedbackTargetType
    trace_id: str
    session_id: str | None = None
    rating: FeedbackRating
    comment: str | None = None

    @field_validator("trace_id")
    @classmethod
    def require_trace_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("trace_id is required.")
        return normalized

    @field_validator("session_id", "comment")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("comment")
    @classmethod
    def limit_comment_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 500:
            raise ValueError("comment must be 500 characters or fewer.")
        return value


class FeedbackResponse(BaseModel):
    status: Literal["ok"]
    feedback_id: str
    created_at: datetime


class StoredFeedbackEntry(BaseModel):
    feedback_id: str
    target_type: FeedbackTargetType
    trace_id: str
    session_id: str | None = None
    rating: FeedbackRating
    comment: str | None = None
    created_at: datetime
