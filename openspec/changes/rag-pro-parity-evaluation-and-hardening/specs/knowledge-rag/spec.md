## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a measurable RAG-Pro parity path

CarbonRag SHALL provide a KnowledgeBase -> Document -> Chunk -> Index -> Search -> Grounded Answer -> Evaluation path that can be measured with fixed test fixtures and metrics.

#### Scenario: User uploads a document directly into a knowledge base

- **WHEN** a user uploads a supported file to `/api/v1/kb/{kb_id}/documents/upload`
- **THEN** CarbonRag creates a `RagDocument` with file metadata and exposes parse, chunk, index progress and errors through document status.

#### Scenario: Workbench generates a grounded test answer

- **WHEN** `/api/v1/rag/test-qa` receives a query with retrieval hits
- **THEN** CarbonRag calls the configured chat provider with grounded evidence and returns answer mode, selected chunks, citations, evidence quality, confidence, and retrieval trace.

#### Scenario: RAG evaluation is run against a fixture

- **WHEN** `/api/v1/rag/eval/run` is called with gold questions or the default fixture
- **THEN** CarbonRag stores a run and returns Hit@1, Hit@3, Recall@5, Precision@5, MRR, citation coverage, no-hit count, vector failure count, and cross-KB leak count.
