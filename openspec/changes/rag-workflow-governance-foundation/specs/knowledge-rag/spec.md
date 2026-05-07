## MODIFIED Requirements

### Requirement: Uploads enter the knowledge task flow
CarbonRag SHALL create knowledge items and ingest tasks for supported user uploads.

#### Scenario: User uploads a file
- **WHEN** upload succeeds
- **THEN** a personal knowledge item and ingest task are created

#### Scenario: Ingest task records workflow checkpoints
- **WHEN** a knowledge ingest task runs
- **THEN** CarbonRag records a workflow run with parse, block, chunk, embedding, vector index, graph candidate, and completion nodes
- **AND** each executed node records status and at least one checkpoint

#### Scenario: Ingest failure identifies failed node
- **WHEN** parsing or indexing fails
- **THEN** the workflow run is marked failed
- **AND** the failed workflow node stores an error message

### Requirement: RAG objects reserve governance metadata
CarbonRag SHALL reserve tenant, owner, visibility, creator, and timestamp metadata on RAG ingest objects without enforcing enterprise RBAC.

#### Scenario: Knowledge item carries governance fields
- **WHEN** a document is created from an upload or shared source
- **THEN** the document can expose `tenant_id`, `owner_user_id`, `visibility`, `created_by`, `created_at`, and `updated_at`

#### Scenario: Knowledge chunk carries governance fields
- **WHEN** chunks are generated for a knowledge item
- **THEN** each chunk can expose `tenant_id`, `owner_user_id`, `visibility`, `created_by`, `created_at`, and `updated_at`

### Requirement: Retrieval traces expose workflow observability fields
CarbonRag SHALL expose lightweight RAG trace fields without requiring OpenTelemetry.

#### Scenario: Retrieval-only trace includes observability fields
- **WHEN** retrieval-only API returns metadata
- **THEN** the trace can include `workflow_id`, `parser_name`, `vector_backend`, `retriever_mode`, `latency_ms`, `fallback_reason`, and `error_code`

#### Scenario: Default ask remains unchanged
- **WHEN** normal ask/session flows run
- **THEN** workflow and governance fields do not change default ask behavior
