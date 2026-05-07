## Why

CarbonRag V1.3 has a protected RAG Lab and a retrieval-only API, but debugging a failed or empty retrieval still requires checking browser and backend logs. V1.3.1 should make the lab self-explanatory by showing the effective backend URL, request parameters, retrieval mode, fallback state, latency, and structured error details without changing `/ask`, session, report, or carbon calculation behavior.

## What Changes

- Add retrieval-only metadata for retriever mode, requested top-k, returned count, fallback status, latency, and source-scope hit counts.
- Return structured retrieval-only errors with controlled public codes/messages while preserving FastAPI validation errors for invalid request payloads.
- Improve the RAG Lab to show `backendBaseUrl`, retrieval endpoint, current request parameters, effective retrieval mode, fallback state, zero-hit guidance, and safe error details.
- Keep existing `chunks`, `references`, and `metadata` response fields additive and backward-compatible.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Extend retrieval-only API observability metadata and structured error handling.
- `frontend-shell-settings`: Extend the protected RAG Lab with backend URL, request parameter, zero-hit, fallback, and error displays.

## Impact

- Affected modules: M5 and M7.
- Apply-stage areas: `backend/app/rag/**`, `backend/app/api/v1/endpoints/rag.py`, `backend/tests/**`, `frontend/src/pages/RagLabPage/**`, `frontend/src/types/rag.ts`, and frontend styles.
- No `/ask`, session, `/generate_report`, `/calc_carbon`, parser, vector store, graph, workflow, authentication, deployment, or infrastructure changes are proposed.
