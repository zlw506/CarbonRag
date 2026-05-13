# Design: RAG-Pro Runtime Performance Hardening

## Runtime Observability

`RagTimingTrace` is the shared diagnostic contract for V1.6.29. It records parse, chunk, embedding, Milvus client, Milvus insert/search, DB chunk loading, sparse retrieval, RRF, rerank, LLM, total timing, candidate counts, Milvus client initialization count, and sparse cache hit state.

The trace is intentionally attached to normal API responses instead of only logs. This lets the frontend explain slow paths without asking developers to inspect backend logs first.

## Pipeline Modes

`quick` is the default ingestion path:

```text
parse -> chunk -> index -> search smoke
```

`acceptance` is the explicit validation path:

```text
parse -> chunk -> index -> search smoke -> eval smoke
```

This prevents the common UX failure where a small document appears "stuck" because the default path also starts evaluation or generation work.

## RAG-Pro Parity Boundary

RAG-Pro remains the implementation spine to port from, but this round keeps CarbonRag boundaries intact: auth, session, AskPage, file, report, OpenSpec, GitNexus, and Mattermost remain CarbonRag-native. Third-party source trees remain ignored and are not committed.
