# Design

CarbonRag keeps the RAG-Pro retrieval stack unchanged: BGE-M3 embedding, Milvus vector runtime, hybrid retrieval, and rerank remain separate from chat generation.

The new local generation path is provider-based:

1. Settings resolve either an account provider or a request-level local provider override.
2. `provider_type=ollama` builds `OllamaChatProvider`.
3. AskPage, `/rag/answer`, and `/rag/test-qa` call the resolved provider.
4. Provider metadata records `provider=ollama`, `model=deepseek-r1:8b`, transport, and optional thinking content.

Native Ollama `/api/chat` is the primary path because it exposes Ollama-specific fields such as `think`, `options.num_ctx`, and `keep_alive`. OpenAI-compatible `/v1/chat/completions` remains available through `provider_type=openai_compatible`.

Local-dev boundary: backend and Ollama must run on the same machine or network-reachable host. A cloud VPS cannot call the user's `localhost:11434`.
