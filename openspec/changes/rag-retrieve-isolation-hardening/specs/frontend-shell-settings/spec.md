## ADDED Requirements

### Requirement: RAG Lab displays only safe retrieval errors
CarbonRag SHALL display retrieval-only failures in RAG Lab using safe error fields from the backend response.

#### Scenario: Backend returns controlled retrieval error
- **WHEN** a RAG Lab retrieval request fails
- **THEN** the frontend displays the HTTP status when available
- **AND** it displays controlled `error`, `error_code`, or `message` values
- **AND** it MUST NOT display raw `backend_detail`, `exception_type`, SQL/driver messages, parser stack details, or local filesystem paths

#### Scenario: Metadata fields are missing
- **WHEN** a retrieval-only response omits optional metadata fields
- **THEN** RAG Lab continues to display chunks, references, safe metadata, zero-hit state, and request parameters without crashing
