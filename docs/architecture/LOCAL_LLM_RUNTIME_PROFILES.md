# Local LLM Runtime Profiles

CarbonRag V1.6.16 switches the default chat runtime direction from a slow cloud proxy to a local open-source chat model profile.

Current status: the local DeepSeek chat model package and Ollama runtime are not yet prepared. This document freezes the supported integration profiles and smoke path; it does not claim that a local chat model is already available on every developer machine.

## Decision

RAG-Pro does not bundle a chat LLM weight package in `3rdparty/RAG-Pro/RAG-Pro`.

RAG-Pro provides:

- local retrieval model defaults: `BAAI/bge-m3`
- local reranker defaults: `BAAI/bge-reranker-v2-m3`
- configurable chat LLM providers: OpenAI-compatible, DeepSeek API, Ollama, vLLM, and similar provider endpoints

CarbonRag therefore keeps BGE-M3 for retrieval and uses a local OpenAI-compatible chat endpoint for answer generation.

## Recommended Route: Ollama + DeepSeek

Use Ollama when the target machine needs the lowest-friction local model runtime.

```env
MODEL_PROVIDER_MODE=openai_compatible
MODEL_API_BASE_URL=http://127.0.0.1:11434/v1
MODEL_API_KEY=ollama-local-key
MODEL_NAME=deepseek-r1:8b
MODEL_TIMEOUT_SECONDS=120
```

Profile file:

```text
.env.llm.ollama-deepseek.example
```

Smoke test:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/llm-smoke-openai-compatible.ps1
```

If Ollama is used through the Settings page instead of `.env`, choose `Ollama`, base URL `http://localhost:11434/api`, and model `deepseek-r1:8b`.

## vLLM Route

Use vLLM when the machine has enough GPU memory and serves a local model through an OpenAI-compatible endpoint.

```env
MODEL_PROVIDER_MODE=openai_compatible
MODEL_API_BASE_URL=http://127.0.0.1:8001/v1
MODEL_API_KEY=vllm-local-key
MODEL_NAME=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
```

Profile file:

```text
.env.llm.vllm-deepseek.example
```

## LM Studio Route

Use LM Studio when a GUI-managed local model is preferred.

```env
MODEL_PROVIDER_MODE=openai_compatible
MODEL_API_BASE_URL=http://127.0.0.1:1234/v1
MODEL_API_KEY=lm-studio-local-key
MODEL_NAME=local-model
```

Profile file:

```text
.env.llm.lmstudio.example
```

## Offline Model Package Placement

Do not commit chat model weights.

Offline chat LLM packages supplied by #1 should be placed under:

```text
data/outputs/models/LLM/<model-name>/
```

Examples:

```text
data/outputs/models/LLM/deepseek-r1-8b/
data/outputs/models/LLM/DeepSeek-R1-Distill-Qwen-7B/
```

Retrieval and rerank model packages remain:

```text
data/outputs/models/BAAI/bge-m3
data/outputs/models/BAAI/bge-reranker-v2-m3
```

`data/outputs/` is ignored by Git. Team members who need offline packages should ask #1 for the archive and extract it to the paths above.

## Acceptance

Before claiming local LLM readiness:

1. Start the local model server.
2. Confirm `MODEL_API_BASE_URL` points to the local OpenAI-compatible endpoint.
3. Run `scripts/llm-smoke-openai-compatible.ps1`.
4. Run a KnowledgeBaseWorkbench Test QA that returns `answer_mode=llm_grounded`.
5. Run AskPage with a selected KB and confirm citations plus retrieval trace.

Cloud chat API fallback is allowed for emergency comparison only. It is not the V1.6.16 default route.

If the project chooses an embedded model-loading route instead of an external local HTTP endpoint, update this document and the `.env.llm.*.example` profiles before asking other teams to reproduce it.
