## 1. OpenSpec

- [x] 1.1 Create review-fix OpenSpec proposal, design, tasks, and delta specs.
- [x] 1.2 Validate the new change strictly.

## 2. Backend Isolation

- [x] 2.1 Remove retrieval-time ingest/sync execution from `/api/v1/rag/retrieve`.
- [x] 2.2 Preserve empty private allowed-id sets through RAG service current/vector/hybrid/fallback paths.
- [x] 2.3 Make private retrieval fail closed when no explicit private knowledge filter is provided.
- [x] 2.4 Make pgvector filter construction fail closed for private empty-selection paths.

## 3. Safe Errors and Frontend

- [x] 3.1 Replace public retrieval-only 500 details with controlled error code and friendly message.
- [x] 3.2 Log internal retrieval exceptions server-side.
- [x] 3.3 Update RAG Lab to avoid rendering backend internals such as `backend_detail` and `exception_type`.

## 4. Tests and Docs

- [x] 4.1 Add backend regression tests for private/mixed empty-selection cross-user isolation.
- [x] 4.2 Update backend runtime-error tests to assert safe error responses.
- [x] 4.3 Update PR/log version wording to `V1.3.X RAG initial baseline`.
- [x] 4.4 Run OpenSpec, backend, and frontend verification.
