## Why

CarbonRag currently has a product-specific BM25 retrieval path, but it does not yet have a reusable RAG engine boundary for vector chunks, graph evidence, reranking, query modes, and structured references. LightRAG provides a mature MIT-licensed architecture pattern for combining document chunks, vector retrieval, knowledge graph entities/relations, and query-mode control; V1.3.0 should establish the smallest CarbonRag-native skeleton before deeper feature work.

## What Changes

- Add a LightRAG-inspired, CarbonRag-native RAG engine proposal under M5 instead of replacing the whole application with the upstream LightRAG package.
- Define a minimal retrieval skeleton with document status, token-oriented chunks, vector chunk retrieval, optional graph candidates, stable references, and retrieval metadata.
- Introduce internal query parameters for `naive` and `mix` modes first; leave `local`, `global`, and `hybrid` graph-first modes for later changes.
- Route embedding and reranking through M1 provider/runtime boundaries instead of direct page-level or retrieval-layer API calls.
- Keep existing public/private/mixed BM25 retrieval as the default fallback while the new engine is experimental.
- Require any future direct LightRAG source reuse to preserve MIT license notices and fit CarbonRag module boundaries.

## Capabilities

### New Capabilities

None. This change extends existing CarbonRag M1/M5/M7 capabilities rather than creating a separate top-level capability.

### Modified Capabilities

- `knowledge-rag`: Add the LightRAG-inspired RAG engine skeleton, query modes, structured retrieval data, fallback rules, and licensing guardrails.
- `ai-runtime`: Add provider-bound embedding and reranker responsibilities needed by the RAG engine.
- `devops-release`: Add optional configuration and safe-default requirements for experimental RAG backends.

## Impact

- Affected modules: M5 primary; M1 and M7 secondary.
- Likely apply-stage code areas: `backend/app/knowledge/**`, `backend/app/retrieval/**`, `backend/app/ai_runtime/**`, `backend/app/runtime_db/**`, API schemas/endpoints, tests, env templates, and docs.
- No breaking change is proposed for existing ask/session behavior in V1.3.0.
- No full LightRAG vendoring is proposed in this change. The implementation may reuse concepts and MIT-compatible code only with preserved notices and review.
