# RAG-Pro Performance Gap Audit V1.6.33

## Scope

V1.6.33 freezes the CarbonRag RAG-Pro baseline. This audit compares the current CarbonRag spine with `3rdparty/RAG-Pro/RAG-Pro` for the parts that still affect delivery confidence: runtime lifecycle, workbench flow, RAG answer path, trace visibility, and handoff boundaries.

RAG-Pro remains the main implementation spine. CarbonRag keeps its own auth, sessions, AskPage, file parsing, citations, reports, OpenSpec, GitNexus, and Mattermost governance.

## Current Baseline

| Area | CarbonRag V1.6.33 | RAG-Pro target | Status |
| --- | --- | --- | --- |
| Knowledge base | `backend/app/rag/kb/*` with KB, document, chunk models and per-KB defaults | KB configuration with embedding/chunk/retrieval settings | Completed |
| Document flow | Upload/import, parse, chunk, index, quick/acceptance pipeline | Upload, status, chunk/index, test chat | Completed |
| Vector runtime | Docker Milvus / Milvus Lite / memory-dev profiles; Milvus client cache by URI | Persistent vector store service | Completed with runtime caveat |
| Adapter lifecycle | `get_vector_store()` now caches adapter by backend/runtime URI | Singleton vector store object | Completed in V1.6.33 |
| Sparse retrieval | KB-level corpus cache and query token cache | Hybrid retrieval cache/optimized index | Partial |
| Answer path | `/rag/answer` and `/rag/test-qa` share grounded provider generation | Generated answer with citations and trace | Completed |
| Legacy path | `/rag/retrieve`, RagLab, `langchain_rag_*` are compatibility-only | No legacy acceptance path | Completed |
| Workbench/Ask consistency | CI test locks same KB and citation path for search/test QA/answer | Same KB in test chat and formal chat | Completed in CI, real Milvus smoke still required |

## V1.6.33 Fixes

### Milvus adapter lifecycle

Evidence:

- `backend/app/rag/retrieval/dense.py`
- `backend/app/rag/vector_backend/milvus_store.py`
- `backend/tests/test_rag_pro_spine_api.py::test_rag_vector_store_adapter_reused`
- `backend/tests/test_rag_pro_spine_api.py::test_warm_search_does_not_reinitialize_milvus_client`

The Milvus client was already cached by URI in `milvus_store.py`. V1.6.33 adds adapter instance reuse in `dense.py`, so the same backend/runtime URI does not rebuild a vector-store adapter on every dense search.

Expected warm-search evidence:

- First search: `milvus_client_init_count = 1`
- Second search on same URI: `milvus_client_init_count = 0`

### Workbench button semantics

Evidence:

- `frontend/src/pages/KnowledgeBaseWorkbench/index.tsx`
- `docs/PLAN/V1.6.33.md`
- `docs/architecture/RAG_RUNTIME_PROFILES.md`

The default workbench action is now `快速建立 RAG`, mapped to the quick pipeline:

```text
parse -> chunk -> index -> search smoke
```

The full acceptance action is now `完整验收 RAG`, mapped to the acceptance pipeline:

```text
parse -> chunk -> index -> search smoke -> eval -> optional generation checks
```

This prevents the normal path from feeling slow because eval or LLM checks were run implicitly.

### Workbench and AskPage consistency

Evidence:

- `backend/tests/test_rag_pro_testqa_and_ask_binding.py::test_workbench_search_testqa_askpage_same_kb_consistency`
- `backend/app/rag/qa/answer.py`

The consistency test uses the fixed acceptance question:

```text
青木制造 2025 年第一季度合计外购电力是多少？
```

It verifies that workbench search, workbench Test QA, and AskPage-equivalent `/rag/answer` use the same `kb_id`, hit the same evidence containing `217,650 kWh`, and return citations from that KB.

## Remaining Gaps

### Real runtime smoke is still environment-gated

CI can prove fake-provider/memory-backend consistency, but real acceptance still requires:

- Docker Desktop running
- Milvus Standalone reachable at `http://127.0.0.1:19530`
- BGE-M3 model available
- bge reranker available if `hybrid_rerank` is selected

If these are missing, the result is an environment blocker, not a proof that RAG-Pro parity failed.

### Chunker parity is not complete

CarbonRag has `recursive` and partial parent-child direction. RAG-Pro has richer modes such as intelligent, table, paper, book, resume, and QA-oriented chunking. These are not part of the V1.6.33 freeze.

### Sparse retrieval is still simpler than RAG-Pro

CarbonRag now has KB-level sparse cache, but it is still Python-side retrieval over indexed chunks. It is acceptable for baseline, but not yet the final high-performance sparse backend.

## Handoff Boundary

#1 keeps ownership of:

- Milvus runtime
- BGE embedding
- reranker
- RAG eval
- AskPage KB binding
- cross-user and cross-KB isolation
- RAG-Pro parity checklist

#3 can take over:

- Workbench visual polish
- empty states
- button layout
- error copy
- progress animation
- citation cards
- mobile adaptation
- ordinary user tutorial copy
