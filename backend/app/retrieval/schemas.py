from typing import Literal

from pydantic import BaseModel, Field


Region = Literal["national", "beijing"]
DocumentType = Literal["policy", "standard", "guideline"]
SourceType = Literal["public_policy", "private_sample"]
SampleType = Literal["doc", "table"]
BusinessTopic = Literal["energy", "production", "logistics", "project_background"]


class PublicPolicyDocumentMetadata(BaseModel):
    doc_id: str
    title: str
    source: str
    source_url: str
    issued_at: str
    region: Region
    doc_type: DocumentType
    filepath: str


class PublicPolicyDocument(BaseModel):
    metadata: PublicPolicyDocumentMetadata
    body: str


class RetrievedChunk(BaseModel):
    doc_id: str
    title: str
    source_type: SourceType
    source: str
    source_url: str | None = None
    issued_at: str | None = None
    region: str | None = None
    doc_type: str | None = None
    sample_type: str | None = None
    business_topic: str | None = None
    chunk_id: str
    snippet: str
    score: float


class RetrievalResult(BaseModel):
    query: str
    top_k: int
    total_hits: int
    hits: list[RetrievedChunk] = Field(default_factory=list)
