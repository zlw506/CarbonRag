# RAG-Pro Parity Checklist V1.6.33

V1.6.33 freezes CarbonRag's RAG-Pro baseline. This checklist records what is ready, what is partial, and what remains outside the baseline.

| Item | Status | Evidence File | Test | Remaining Risk |
| --- | --- | --- | --- | --- |
| Knowledge base creation | Completed | `backend/app/api/v1/endpoints/kb.py`, `backend/app/rag/kb/storage.py` | `test_kb_defaults_upload_status_answer_and_eval` | None for baseline |
| KB config: `embedding_model`, `chunk_size`, `chunk_overlap`, `rerank_top_n`, `retrieval_top_k` | Completed | `backend/app/rag/kb/models.py` | `test_kb_defaults_upload_status_answer_and_eval` | UI advanced editing can improve later |
| Direct document upload | Completed | `backend/app/api/v1/endpoints/kb.py` | `test_kb_defaults_upload_status_answer_and_eval` | Large-file async queue is future work |
| Document status display | Completed | `frontend/src/pages/KnowledgeBaseWorkbench/index.tsx` | frontend typecheck/build | Copy and empty-state polish handed to #3 |
| Parse | Completed | `backend/app/rag/spine.py`, `backend/app/rag/documents/service.py` | `test_kb_document_pipeline_runs_all_stages_and_reports_smoke` | Parser quality varies by file type |
| Chunk | Completed | `backend/app/rag/documents/chunking.py` | `test_kb_document_pipeline_runs_all_stages_and_reports_smoke` | RAG-Pro advanced modes are partial |
| Index | Completed | `backend/app/rag/vector_backend/milvus_store.py` | `test_kb_document_pipeline_runs_all_stages_and_reports_smoke` | Real Milvus/BGE required for production acceptance |
| Quick pipeline | Completed | `backend/app/rag/spine.py` | `test_kb_document_pipeline_runs_all_stages_and_reports_smoke` | None for synchronous baseline |
| Acceptance pipeline | Completed | `backend/app/rag/spine.py` | `test_kb_document_pipeline_runs_all_stages_and_reports_smoke` | Eval cases must be curated |
| Search | Completed | `backend/app/api/v1/endpoints/rag.py`, `backend/app/rag/spine.py` | `test_kb_document_status_and_test_qa` | Quality depends on chunking/model availability |
| Test QA | Completed | `backend/app/rag/spine.py`, `backend/app/rag/qa/test_qa.py` | `test_rag_test_qa_calls_chat_provider_with_grounded_context` | Provider outage returns degraded/retrieval-only |
| Answer | Completed | `backend/app/rag/spine.py`, `backend/app/rag/qa/answer.py` | `test_kb_defaults_upload_status_answer_and_eval` | Provider quality is model-dependent |
| AskPage uses selected KB | Completed | `backend/app/api/v1/endpoints/sessions.py`, `frontend/src/pages/AskPage/*` | `test_ask_page_selected_kb_is_passed_to_runtime` | Real UI smoke still recommended |
| Citations | Completed | `backend/app/rag/qa/answer.py` | `test_workbench_search_testqa_askpage_same_kb_consistency` | Citation card UX handed to #3 |
| Timing trace | Completed | `backend/app/rag/kb/models.py`, `backend/app/rag/spine.py` | `test_kb_document_pipeline_runs_all_stages_and_reports_smoke` | Needs real runtime profile logs in acceptance |
| Eval run | Completed | `backend/app/rag/eval.py`, `backend/app/api/v1/endpoints/rag.py` | `test_kb_defaults_upload_status_answer_and_eval` | Gold set must grow beyond Qingmu fixture |
| Ollama provider | Completed for local-dev | `backend/app/ai_runtime/providers/chat_ollama.py`, `docs/architecture/LOCAL_LLM_PROVIDER_ARCHITECTURE.md` | provider tests / local smoke | Cloud VPS cannot access user localhost |
| Milvus Docker | Completed as target profile | `docs/architecture/RAG_RUNTIME_PROFILES.md`, `scripts/rag-start-milvus-docker-windows.ps1` | local smoke script | Docker/Milvus must be running before real E2E |
| Milvus adapter reuse | Completed in V1.6.33 | `backend/app/rag/retrieval/dense.py`, `backend/app/rag/vector_backend/milvus_store.py` | `test_rag_vector_store_adapter_reused`, `test_warm_search_does_not_reinitialize_milvus_client` | None for adapter/client lifecycle |
| Legacy `/rag/retrieve` hidden | Completed | `backend/app/api/v1/endpoints/rag.py`, frontend navigation | legacy/admin tests | Keep compatibility only |

## Baseline Verdict

CarbonRag can now describe its RAG-Pro spine as a baseline-ready RAG path when these conditions hold:

- Docker Milvus is reachable.
- BGE-M3 embedding is available.
- Reranker availability is reflected honestly in trace.
- `degraded=false` for real acceptance.
- Workbench search, Workbench Test QA, and AskPage use the same selected `kb_id`.

## Handoff

Keep under #1:

- Milvus runtime
- BGE embedding
- reranker
- RAG eval
- AskPage KB binding
- cross-user / cross-KB isolation
- this parity checklist

Hand off to #3:

- Workbench visual optimization
- error copy
- progress animations
- citation card presentation
- empty state
- button layout
- mobile adaptation
- ordinary user onboarding guide
