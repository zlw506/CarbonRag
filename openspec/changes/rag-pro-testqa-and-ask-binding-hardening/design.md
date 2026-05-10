# Design: RAG-Pro Test QA and Ask Binding Hardening

## Ask Binding

`AskRequest.kb_id` and `AskRequest.rag_mode` remain optional public request fields. The session endpoint must keep copying them into `ChatRequest.payload`, and AI Runtime must pass them to RAG tool arguments. Regression tests cover both the payload and the runtime tool argument surface.

## Test QA

`/api/v1/rag/test-qa` is a workbench validation endpoint. It does not write to session history. It uses the same RAG-Pro spine search path as `/rag/search`, then:

1. If no chunks are retrieved, returns `answer_mode=no_hits`, selected chunks empty, citations empty, and does not call the chat provider.
2. If chunks are retrieved, builds a grounded prompt with chunk ids, titles, location metadata, and snippets.
3. Calls the configured chat provider.
4. Returns `answer_mode=llm_grounded` on success.
5. Returns `answer_mode=retrieval_only` with provider error warnings when provider generation fails, without pretending an LLM answer was produced.

Evidence quality is heuristic and transparent. It is derived from hit count, rerank state, and degradation warnings.

## Legacy RAG Lab

`/rag/retrieve` and `RagLabPage` stay available only as an admin legacy experiment. They are not the formal RAG-Pro acceptance path.
