## MODIFIED Requirements

### Requirement: Frontend exposes protected RAG retrieval lab
CarbonRag SHALL provide an authenticated workbench surface for retrieval-only RAG validation with visible backend, request, mode, fallback, zero-hit, error, and vector adapter observability.

#### Scenario: Retrieval backend falls back
- **WHEN** the retrieval-only API response records disabled, unavailable, current, fake, or fallback backend state
- **THEN** the frontend displays vector, graph, rerank, `fallback_used`, `fallback_reason`, vector backend, vector adapter name, and vector backend health so users can verify the active RAG path
