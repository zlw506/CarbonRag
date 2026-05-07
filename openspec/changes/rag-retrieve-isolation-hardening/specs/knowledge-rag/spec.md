## ADDED Requirements

### Requirement: Retrieval-only private scope fails closed
CarbonRag SHALL preserve private knowledge filters across retrieval-only current, BM25, vector, pgvector, hybrid, and fallback paths so an empty private selection means no private candidates.

#### Scenario: Empty private selection returns no private chunks
- **WHEN** a user calls retrieval-only RAG with private scope and no selected private knowledge items
- **THEN** CarbonRag returns no private chunks
- **AND** it MUST NOT treat the empty selection as unrestricted private retrieval

#### Scenario: Mixed empty selection excludes private chunks
- **WHEN** a user calls retrieval-only RAG with mixed scope and no selected private knowledge items
- **THEN** CarbonRag may return public chunks
- **AND** it MUST NOT return any personal knowledge chunk from another user

#### Scenario: Cross-user personal knowledge remains isolated
- **WHEN** user A has indexed personal knowledge
- **AND** user B calls `/api/v1/rag/retrieve` with private or mixed scope and an empty private selection
- **THEN** user B MUST NOT receive user A's personal chunks

### Requirement: Retrieval-only API is read-only over indexed knowledge
CarbonRag SHALL keep `/api/v1/rag/retrieve` read-only over currently indexed knowledge.

#### Scenario: Retrieval request does not run ingest work
- **WHEN** a user calls `/api/v1/rag/retrieve`
- **THEN** the request MUST NOT synchronously run upload sync, parser ingest, queued task execution, or index rebuild work
- **AND** ingestion failures MUST NOT be swallowed inside the retrieval request path

### Requirement: Retrieval-only errors are safe for users
CarbonRag SHALL return controlled retrieval-only error codes and friendly messages without exposing internal exception details to normal users.

#### Scenario: Unexpected retrieval failure
- **WHEN** retrieval-only execution raises an unexpected exception
- **THEN** CarbonRag logs the internal exception server-side
- **AND** the HTTP response contains only a stable error code and safe user-facing message
- **AND** the HTTP response MUST NOT include raw exception text, exception type, SQL/driver detail, parser paths, or local filesystem paths
