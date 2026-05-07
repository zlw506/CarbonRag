## Scope

This change establishes a local, repeatable retrieval evaluation baseline and a safe rerank provider boundary. It does not add a production rerank model.

## Rerank Provider Strategy

- Keep the existing `BaseRerankProvider` AI runtime abstraction as the canonical provider interface.
- Add `NoopRerankProvider` that preserves candidate order and reports skipped/no-op metadata.
- Add `FakeRerankProvider` that applies deterministic keyword-overlap scoring for tests and local evaluation.
- Keep the provider factory default as no-op/disabled so local development and `/ask` behavior do not change.

## Evaluation Strategy

- Store fixed cases under `data/eval/rag/rag_eval_cases.json`.
- Each case includes an id, query, knowledge scope, expected document ids, and expected keywords.
- `scripts/rag_eval.py` loads the dataset, runs configured retrieval variants, and emits metrics:
  - `total_cases`
  - `hit_at_1`
  - `hit_at_3`
  - `hit_at_5`
  - `citation_count`
  - `zero_hit_count`
  - `fallback_count`
  - `average_latency_ms`

## Non-Goals

- No network-only reranker.
- No mandatory large model or new heavy dependency.
- No GraphRAG, Neo4j, LangGraph, calc/report/session changes.
