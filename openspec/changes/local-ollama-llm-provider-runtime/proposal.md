# Change: local-ollama-llm-provider-runtime

## Why

Cloud chat generation latency is blocking RAG validation. CarbonRag needs a local-dev generation route that can use Ollama `deepseek-r1:8b` for AskPage and RAG-Pro grounded answers without changing the BGE/Milvus retrieval stack.

## What Changes

- Add a native Ollama chat provider using `/api/chat`, including streaming and thinking metadata.
- Dispatch the chat provider factory by configured provider type instead of always using OpenAI-compatible transport.
- Make `/rag/answer` and `/rag/test-qa` use the current user's active provider or request-level local provider override.
- Add an Ollama / DeepSeek-R1 8B provider template to the Settings page.
- Add local Ollama environment profile, smoke scripts, architecture notes, and V1.6.17 plan.

## Out Of Scope

- No embedding, Milvus, reranker, carbon accounting, or new RAG-Pro field work.
- No model weights are committed.
- Cloud VPS does not automatically reach a user's local Ollama endpoint.
