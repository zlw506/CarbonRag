## ADDED Requirements

### Requirement: Frontend exposes protected RAG retrieval lab
CarbonRag SHALL provide an authenticated workbench surface for retrieval-only RAG validation.

#### Scenario: User runs a retrieval lab query
- **WHEN** an authenticated user submits a question with retrieval mode, knowledge scope, top-k, and rerank settings
- **THEN** the frontend calls a retrieval-only API and displays returned chunks, references, and retrieval metadata without requesting chat completion

#### Scenario: Retrieval backend falls back
- **WHEN** the retrieval-only API response records disabled, unavailable, or fallback backend state
- **THEN** the frontend displays vector, graph, rerank, and fallback status so users can verify the active RAG path

#### Scenario: User inspects request target and retrieval path
- **WHEN** the RAG Lab is open
- **THEN** the frontend displays the API base URL, retrieval endpoint, active retrieval path, and zero-hit guidance when no chunks are returned

#### Scenario: Knowledge item filters respect visible scope
- **WHEN** the user selects private or mixed retrieval with specific knowledge items
- **THEN** the frontend sends only selected visible knowledge item ids and keeps public-only retrieval independent from private filters
