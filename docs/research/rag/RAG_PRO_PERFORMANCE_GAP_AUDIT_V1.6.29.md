# V1.6.29 RAG-Pro Performance Gap Audit

## Scope

This audit compares CarbonRag's V1.6.29 RAG runtime with the local RAG-Pro reference at `3rdparty/RAG-Pro/RAG-Pro`. RAG-Pro remains the main implementation spine for V1.6.x RAG work, but CarbonRag keeps its own auth, session, AskPage, file, report, OpenSpec, GitNexus, and Mattermost boundaries.

## High-Risk Runtime Gaps

| Area | RAG-Pro reference | CarbonRag before V1.6.29 | V1.6.29 action |
| --- | --- | --- | --- |
| Vector store lifecycle | `core/vector_store.py` keeps a long-lived vector store/client object. | `MilvusVectorStoreAdapter` created a `MilvusClient` on every index/search call. | Cache Milvus clients by URI and expose `milvus_client_init_count` in timing trace. |
| Sparse retrieval | RAG-Pro routes retrieval through the configured retriever/vector store path. | `sparse_search()` rebuilt token counters by scanning chunks on every query. | Cache sparse corpus by KB/chunk watermark and expose `sparse_cache_hit`. |
| Runtime profiling | RAG-Pro has a clearer core pipeline separation, making slow points easier to infer. | CarbonRag returned hit counts but no stage timing. | Add `RagTimingTrace` for pipeline/search/answer/test QA. |
| Pipeline default | RAG-Pro separates document processing from test chat. | CarbonRag one-click pipeline attempted eval smoke when cases existed, making the default path unexpectedly heavy. | Split `quick` and `acceptance` pipeline modes; default quick skips eval/LLM. |
| Frontend operation labels | RAG-Pro document/test flows are more explicit. | CarbonRag default button implied full acceptance and could look stuck. | Workbench now uses "快速入库" by default and "验收评分入库" explicitly. |

## API Contract Status

CarbonRag frontend `frontend/src/services/kb.ts` calls the following KB APIs:

- `POST /api/v1/kb/{kb_id}/documents/upload`
- `GET /api/v1/kb/{kb_id}/documents/{doc_id}/status`
- `POST /api/v1/kb/{kb_id}/documents/{doc_id}/run-pipeline`
- `POST /api/v1/kb/{kb_id}/documents/run-pipeline-batch`

V1.6.29 confirms these backend endpoints exist and adds regression coverage for the pipeline mode contract. The remaining contract risk is response drift: frontend and backend must keep `pipeline_mode`, `timing_trace`, `failed_stage`, `warnings`, and counts aligned.

## Legacy Paths

The following paths remain compatibility/diagnostic routes and are not V1.6.x acceptance evidence:

- `/api/v1/rag/retrieve`
- `RagLabPage` / Legacy RAG experiment page
- `langchain_rag_search`
- `langchain_rag_answer`

Formal RAG-Pro acceptance remains:

- `KnowledgeBaseWorkbench`
- `AskPage`
- `/api/v1/rag/search`
- `/api/v1/rag/answer`
- `/api/v1/rag/test-qa`
- `/api/v1/rag/eval/run`

## Chunker Gap

RAG-Pro exposes multiple chunking strategies. CarbonRag currently supports the RAG-Pro parity fields and the existing recursive/parent-child direction, but it does not yet port the full RAG-Pro strategy set such as book, paper, resume, table, QA, and intelligent modes. This is intentionally not expanded in V1.6.29; performance observability comes first.

## Answer Gap

CarbonRag `/rag/answer` now routes through the shared grounded answer path used by Test QA. If the provider is unavailable, it must return `answer_mode=retrieval_only` and preserve retrieval trace rather than pretending that a full LLM answer was generated.

## V1.6.29 Acceptance Evidence

This round is not complete unless validation shows:

- KB pipeline quick mode does not run eval/LLM.
- Acceptance mode is the only mode that attempts eval smoke.
- Warm Milvus search reports `milvus_client_init_count=0`.
- Repeated sparse search can report `sparse_cache_hit=true`.
- Workbench can display timing and cache trace fields.
- `logs/rag/profile-v1.6.29.json` can be produced by the profile scripts.
