## Context

The current V1.3.X RAG branch adds retrieval-only APIs, RAG Lab, vector adapter boundaries, hybrid retrieval, optional parser providers, graph experiments, and workflow foundations. #1 review identified that the retrieval-only path could turn an empty private selection into an unrestricted private search through `set(...) or None`. The same route also performed ingest work during retrieval and exposed internal exception details in HTTP responses.

## Goals / Non-Goals

**Goals:**

- Make empty private selection semantics explicit and consistent: `[]` or `set()` means no private candidates.
- Keep private/mixed retrieval scoped to selected visible knowledge item ids or session-bound knowledge ids.
- Keep retrieval-only read-only over indexed state.
- Keep public HTTP errors controlled while preserving server-side diagnostics through logs.
- Add regression tests for cross-user and empty-selection leak paths.
- Align PR/log wording with the broad V1.3.X baseline scope.

**Non-Goals:**

- No new RAG feature work.
- No changes to `/ask`, session, report, or `calc_carbon` behavior.
- No new parser, vector, graph, auth, workflow, deployment, or database dependency.
- No full RBAC implementation.

## Decisions

- **Preserve empty sets through the service layer.** Retrieval code will avoid `set(...) or None` for private filters. `None` remains reserved for explicitly public paths or legacy internal calls; private/mixed paths receive an explicit set, including an empty set.
- **Fail closed for private retrieval.** `PrivateSampleRetriever.search()` will return no private hits when neither `allowed_knowledge_item_ids` nor `allowed_doc_ids` is provided. This prevents any caller from accidentally receiving all personal knowledge.
- **Apply pgvector filters fail-closed.** `PgVectorStoreAdapter` will treat empty private allowed ids as `WHERE 1 = 0` for private-only searches and as public-only for mixed searches.
- **Keep retrieval read-only.** The retrieval route will not call upload sync, shared-sample sync, queued task execution, or cache clearing. Indexing remains owned by knowledge task/background flows or explicit management actions.
- **Log, do not disclose, internals.** Unexpected retrieval exceptions will be logged with stack traces. HTTP responses will contain a stable error code and friendly message only.
- **Frontend displays safe error fields.** RAG Lab will display HTTP status plus controlled `error`, `error_code`, and `message` fields, but not `backend_detail` or `exception_type`.

## Risks / Trade-offs

- **Risk: existing manual private RAG tests without selected knowledge may now return zero hits.** This is intended; users must select visible private knowledge or use public/mixed public evidence.
- **Risk: removing retrieval-time sync may make just-uploaded content unavailable until its ingest task completes.** This matches the desired read-only retrieval contract; failed/stale ingest belongs in task status, not hidden in retrieval.
- **Risk: legacy internal callers may pass `None` expecting unrestricted private access.** Private retriever now fails closed, and tests cover the route and fallback semantics.
