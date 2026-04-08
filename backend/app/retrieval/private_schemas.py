from pydantic import BaseModel

from app.retrieval.schemas import BusinessTopic, SampleType


class PrivateSampleDocumentMetadata(BaseModel):
    doc_id: str
    title: str
    source_type: str
    sample_type: SampleType
    business_topic: BusinessTopic
    filepath: str
    session_attachable: bool


class PrivateSampleDocument(BaseModel):
    metadata: PrivateSampleDocumentMetadata
    body: str


class PrivateSampleCatalogItem(BaseModel):
    doc_id: str
    title: str
    source_type: str
    sample_type: SampleType
    business_topic: BusinessTopic
    session_attachable: bool
