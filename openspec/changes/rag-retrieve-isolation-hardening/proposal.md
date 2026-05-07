## Why

PR #3 review found a blocking data isolation risk in retrieval-only private/mixed RAG: an empty private selection could be converted into unrestricted private retrieval, and runtime errors were exposed to normal users. This change hardens the V1.3.X RAG baseline before it can be merged.

## What Changes

- Preserve empty private knowledge selections as "no private candidates" across current/BM25, vector, pgvector, hybrid, and fallback retrieval paths.
- Make `/api/v1/rag/retrieve` read-only over already indexed knowledge instead of synchronously running ingest or rebuild work on each request.
- Return controlled public error codes/messages from retrieval-only failures while logging internal exception details server-side.
- Update RAG Lab error display so backend internals such as exception type, SQL/driver errors, paths, or parser details are not shown to ordinary users.
- Rename the PR/log scope from a narrow `V1.3.1` patch to the broader `V1.3.X RAG initial baseline`, with the concrete change-id set listed.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `knowledge-rag`: Harden retrieval-only private isolation, read-only retrieval semantics, and controlled error responses.
- `frontend-shell-settings`: Harden RAG Lab error display while preserving metadata/chunk/reference observability.
- `governance`: Clarify that PR version labels must match the actual version/change-id scope.

## Impact

- Affected modules: M3 Frontend Chat UX, M5 Knowledge/File/RAG, M8 Governance.
- Backend areas: `backend/app/api/v1/endpoints/rag.py`, `backend/app/rag/service.py`, `backend/app/rag/vector_store.py`, `backend/app/retrieval/private_retriever.py`, and tests.
- Frontend areas: `frontend/src/pages/RagLabPage/**`.
- Documentation areas: `日志/#2/**` and PR title/body.
- No `/ask` default behavior change, no `calc_carbon`, no report/session changes, no new heavy dependencies, no new vector or graph backend.
