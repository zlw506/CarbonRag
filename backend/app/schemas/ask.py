from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


KnowledgeScope = Literal["public", "private_sample", "mixed"]
AskStatus = Literal["ok", "provider_error", "invalid_input"]


class AskCitation(BaseModel):
    source_id: str
    title: str
    snippet: str


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    knowledge_scope: KnowledgeScope = "public"
    top_k: int = Field(default=5, ge=1)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        return value.strip()


class AskResponse(BaseModel):
    answer: str
    mode: Literal["ask"]
    status: AskStatus
    citations: list[AskCitation] = Field(default_factory=list)
    trace_id: str
