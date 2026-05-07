## Context

CarbonRag's current M5 implementation indexes uploaded/private sample files into local knowledge chunks and searches them with BM25. This is enough for the MVP, but it cannot support LightRAG-style retrieval modes, vector recall, entity/relation graph evidence, reranking, or retrieval-only debugging data.

LightRAG's useful pattern is the separation of storage and retrieval responsibilities: document/status storage, text chunk storage, vector storage for chunks/entities/relations, graph storage for entity relations, query parameters, and structured references. CarbonRag should adopt that shape in a smaller form that respects the existing auth, session, AI runtime, and deployment boundaries.

## Goals / Non-Goals

**Goals:**

- Establish an M5 RAG engine boundary that can evolve toward LightRAG-style retrieval.
- Add a minimal `naive` and `mix` query-mode contract before implementing graph-heavy `local`, `global`, or `hybrid` modes.
- Keep existing BM25 public/private/mixed retrieval available as fallback.
- Route embedding and rerank calls through M1 provider abstractions.
- Return structured retrieval data that can be tested without calling a chat model.
- Expose a protected frontend RAG Lab for retrieval-only validation of chunks, references, and backend status.
- Establish minimal enterprise RAG contracts and adapter boundaries before adding heavy third-party runtime dependencies.
- Keep the change additive and easy to roll back.

**Non-Goals:**

- Do not replace CarbonRag with the upstream LightRAG package.
- Do not vendor LightRAG source code in the proposal stage.
- Do not add Neo4j, Milvus, Qdrant, Redis, OpenSearch, RAGAS, Langfuse, multimodal parsing, or graph viewer UI in V1.3.0.
- Do not remove existing BM25 retrieval or change public ask behavior by default.
- Do not perform full historical reindexing without a separate reviewed migration plan.

## Decisions

### Decision 1: Adopt the architecture shape, not the whole package

CarbonRag will define its own small RAG engine interfaces inspired by LightRAG. This avoids forcing LightRAG's server, workspace, storage, and UI assumptions into CarbonRag's existing auth/session/carbon-report product.

Alternative considered: depend directly on `lightrag-hku` and call `LightRAG` as a black box. Rejected for V1.3.0 because it would blur module ownership, duplicate API server concerns, and make rollback harder.

### Decision 2: Keep M5 as owner of retrieval state; M1 owns model calls

M5 will own knowledge items, document status, chunks, retrieval modes, evidence references, and graph/vector index state. M1 will own embedding and rerank provider access, retries, timeouts, and model configuration. Retrieval code must not call external model APIs directly.

Alternative considered: let M5 instantiate embedding clients directly. Rejected because it duplicates provider settings and violates current AI runtime boundaries.

### Decision 3: Start with `naive` and `mix`

`naive` means vector-first chunk retrieval when embedding/index support is configured, with BM25 fallback while experimental support is unavailable. `mix` means vector chunks plus optional graph candidates and merged references; graph candidates may be empty in the first implementation.

Alternative considered: implement LightRAG's full `local`, `global`, `hybrid`, `naive`, and `mix` set immediately. Rejected because entity extraction, graph merge, deletion rebuild, and prompt tuning are separate high-risk work.

### Decision 4: Retrieval data is separate from answer generation

The new engine will expose structured retrieval data before the chat model is called: chunks, references, scores, mode, provider availability, and fallback reason. This lets tests and future UI/debug panels inspect retrieval quality without paying for LLM generation.

Alternative considered: only pass formatted text into the ask prompt. Rejected because it hides retrieval failures and makes RAG quality hard to test.

### Decision 5: Experimental configuration must be safe by default

The new engine should be off or fallback-safe until configured. Missing embedding/rerank settings, unavailable optional dependencies, or empty vector indexes must not break existing public/private ask flows.

Alternative considered: make vector retrieval mandatory once code lands. Rejected because existing local/cloud deployments can build today and should not be blocked by optional RAG infrastructure.

### Decision 6: Preserve third-party license notices

LightRAG is MIT licensed. If apply-stage work copies or adapts substantial LightRAG code, the PR must preserve copyright/license notices and document the source scope. Pure architectural inspiration still records the source in design/review notes.

### Decision 7: Add a retrieval lab before graph viewer or document manager

CarbonRag will first expose a small protected RAG Lab rather than copying LightRAG's full WebUI. The lab focuses on the feedback loop V1.3 needs most: submit a question, select mode/scope/top-k/rerank settings, inspect chunks/references, and confirm vector/graph/rerank/fallback states.

Alternative considered: port LightRAG's complete WebUI including document management and graph visualization. Rejected for this change because CarbonRag already owns auth, knowledge management, sessions, and product navigation; a full port would duplicate surfaces before the retrieval engine is ready.

### Decision 8: Add contracts and disabled adapters before real providers

The enterprise RAG roadmap from `deep-research-report.md` will start with CarbonRag-native contracts for parsed documents, chunks, embeddings, citations, traces, parser providers, vector store adapters, graph index builders, and workflow checkpoints. V1.3.x will add disabled or lightweight local implementations so local/cloud deployments keep working without Docling, MinerU, pgvector, Qdrant, Neo4j, LangGraph, or Haystack installed.

Alternative considered: install and configure Docling, pgvector, Neo4j, and LangGraph immediately. Rejected for this change because the repository first needs stable module contracts, OpenSpec acceptance points, and RAG Lab observability before introducing heavier runtime dependencies.

## Risks / Trade-offs

- [Scope creep] LightRAG is large and includes server, WebUI, storage backends, graph editing, evaluation, and observability. -> Keep V1.3.0 to contracts and minimal backend skeleton.
- [Model cost] Entity extraction, embedding, and reranking can trigger expensive calls. -> Use provider gates, test fakes, and retrieval-only validation.
- [Data migration risk] New vector/graph tables may diverge from existing knowledge chunks. -> Additive schema only; existing BM25 path remains valid.
- [Quality regression] New retrieval modes could change answers. -> Default to existing behavior unless experimental mode is explicitly enabled.
- [Dependency weight] Full LightRAG optional storage stack is heavy. -> Do not import the full stack in V1.3.0; add narrow dependencies only after review.
- [Roadmap overreach] The enterprise plan spans multiple versions. -> In this change, implement only stable contracts, safe disabled adapters, and RAG Lab visibility improvements.

## Migration Plan

1. Proposal stage: add OpenSpec deltas and design only.
2. Apply stage: add additive schemas/services behind experimental flags and fallback defaults.
3. Add tests for query params, retrieval data shape, fallback behavior, and provider boundary calls using fakes.
4. Add a protected frontend RAG Lab page that mirrors LightRAG's retrieval testing workflow at CarbonRag scale.
5. Add enterprise foundation contracts and disabled adapters for parser, vector store, graph, and workflow layers without changing default ask/session behavior.
6. Update env templates and docs if any optional setting is introduced.
7. Rollback by disabling the experimental RAG mode or reverting the additive branch; existing BM25 retrieval and ask pages remain available.

## Open Questions

- Which persistent vector backend should be first for production: PostgreSQL/pgvector, local file-backed vector storage, or a small in-repo adapter?
- Should later V1.3 changes add LightRAG-style graph visualization after entity/relation extraction exists?
- Should graph records be stored in runtime DB first, or deferred until the entity/relation extraction change?
