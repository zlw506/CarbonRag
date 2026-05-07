# Tasks

## Proposal

- [x] Create V1.6.0 OpenSpec change for rerank provider and RAG eval baseline.
- [x] Confirm BM25, vector, hybrid, and existing optional rerank hook exist.

## Apply

- [x] Add Noop/Fake rerank providers behind the existing AI runtime rerank boundary.
- [x] Keep the default rerank provider no-op/disabled.
- [x] Add fixed RAG eval cases with at least 10 public-policy and 5 private-sample questions.
- [x] Add `scripts/rag_eval.py` with JSON/Markdown metrics output.
- [x] Add tests for Noop and Fake rerank providers.
- [x] Add tests for eval script normal and empty dataset behavior.
- [x] Confirm `/ask` default behavior is unchanged.
- [x] Run `openspec validate rerank-provider-rag-eval --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build if frontend types are touched.
- [x] Commit locally without push or PR.
