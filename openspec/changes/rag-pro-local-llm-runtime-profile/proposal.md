# Change: rag-pro-local-llm-runtime-profile

## Why

Cloud chat API latency is blocking RAG development feedback. CarbonRag needs a local open-source chat LLM route that matches RAG-Pro's provider-based model configuration without committing model weights.

## What Changes

- Default development chat generation is documented and configured for a local OpenAI-compatible endpoint.
- Add Ollama, vLLM, and LM Studio runtime profiles.
- Add smoke scripts that verify `/v1/chat/completions` against the selected local model.
- Document that RAG-Pro does not bundle chat LLM weights; offline chat model packages must be distributed out of band by #1.
- Keep BGE-M3 and bge-reranker as retrieval/rerank model assets, not chat LLMs.

## Out Of Scope

- No model weights are committed.
- No ragPdfSystem runtime migration.
- No new RAG facade or knowledge graph UI.

