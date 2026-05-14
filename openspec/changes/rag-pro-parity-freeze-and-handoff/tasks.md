# Tasks: rag-pro-parity-freeze-and-handoff

## 1. Version and Governance

- [x] Update `README.md` to V1.6.33 baseline status.
- [x] Add `docs/PLAN/V1.6.33.md`.
- [x] Add V1.6.33 runtime/profile freeze note.
- [x] Add V1.6.33 RAG-Pro performance gap audit.
- [x] Add V1.6.33 RAG-Pro parity checklist.

## 2. Workbench Semantics

- [x] Rename quick pipeline entry to `快速建立 RAG`.
- [x] Rename acceptance pipeline entry to `完整验收 RAG`.
- [x] Keep quick pipeline free of LLM/eval work.
- [x] Keep acceptance pipeline explicit.

## 3. Milvus Lifecycle Evidence

- [x] Reuse vector store adapter by backend/runtime URI.
- [x] Keep Milvus client cache by URI.
- [x] Add `test_rag_vector_store_adapter_reused`.
- [x] Add `test_warm_search_does_not_reinitialize_milvus_client`.

## 4. Workbench and AskPage Consistency

- [x] Add consistency test for Qingmu `217,650 kWh`.
- [x] Ensure citations carry `kb_id`.
- [x] Confirm search, Test QA, and answer use the same selected KB.

## 5. Validation

- [x] `openspec validate rag-pro-parity-freeze-and-handoff --strict`
- [x] `openspec validate --all`
- [x] Targeted backend pytest.
- [x] Frontend typecheck/build.
- [x] `git diff --check`
- [x] `gitnexus detect_changes`
