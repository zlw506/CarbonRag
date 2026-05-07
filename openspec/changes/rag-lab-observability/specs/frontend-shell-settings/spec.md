## MODIFIED Requirements

### Requirement: Frontend exposes protected RAG retrieval lab
CarbonRag SHALL provide an authenticated workbench surface for retrieval-only RAG validation with visible backend, request, mode, fallback, zero-hit, and error observability.

#### Scenario: User runs a retrieval lab query
- **WHEN** an authenticated user submits a question with retrieval mode, knowledge scope, top-k, and rerank settings
- **THEN** the frontend calls a retrieval-only API and displays returned chunks, references, retrieval metadata, the actual backend base URL, and the retrieval endpoint without requesting chat completion

#### Scenario: Retrieval backend falls back
- **WHEN** the retrieval-only API response records disabled, unavailable, or fallback backend state
- **THEN** the frontend displays vector, graph, rerank, `fallback_used`, and `fallback_reason` status so users can verify the active RAG path

#### Scenario: User inspects request target and retrieval path
- **WHEN** the RAG Lab is open
- **THEN** the frontend displays the API base URL, backend base URL, retrieval endpoint, current request parameters, active retrieval mode, active retrieval path, and zero-hit guidance when no chunks are returned

#### Scenario: Retrieval returns no chunks
- **WHEN** retrieval-only returns zero chunks
- **THEN** the frontend displays `未检索到相关片段` instead of leaving the result area blank

#### Scenario: Retrieval request fails
- **WHEN** the retrieval-only request returns a validation, authorization, or backend error
- **THEN** the frontend displays HTTP status when available and a controlled error message
- **AND** the frontend does not render backend internals such as raw exception text, `backend_detail`, or `exception_type`

#### Scenario: Knowledge item filters respect visible scope
- **WHEN** the user selects private or mixed retrieval with specific knowledge items
- **THEN** the frontend sends only selected visible knowledge item ids and keeps public-only retrieval independent from private filters
