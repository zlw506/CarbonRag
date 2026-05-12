# Local LLM Runtime Profiles

CarbonRag V1.6.17 promotes Ollama native chat API to the default local-dev generation route.

## Decision

RAG-Pro does not bundle a chat LLM weight package in `3rdparty/RAG-Pro/RAG-Pro`.

RAG-Pro provides:

- local retrieval model defaults: `BAAI/bge-m3`
- local reranker defaults: `BAAI/bge-reranker-v2-m3`
- configurable chat LLM providers: OpenAI-compatible, DeepSeek API, Ollama, vLLM, LM Studio, and similar endpoints

CarbonRag therefore keeps BGE-M3 for retrieval and uses Ollama `deepseek-r1:8b` for local answer generation.

## Recommended Route: Ollama Native API

Use this profile when the backend and Ollama run on the same developer machine.

```env
AI_CHAT_PROVIDER=ollama
MODEL_PROVIDER_MODE=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_TIMEOUT_SECONDS=180
OLLAMA_NUM_CTX=8192
OLLAMA_KEEP_ALIVE=10m
OLLAMA_THINK=true
RAG_GENERATION_PROVIDER=ollama
RAG_GENERATION_MODEL=deepseek-r1:8b
```

Profile file:

```text
.env.llm.ollama-local.example
```

Smoke test:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/llm-ollama-smoke.ps1
```

The smoke checks `/api/tags` and `/api/chat`, and verifies that the model tag `deepseek-r1:8b` exists.

## Ollama OpenAI-Compatible Route

Use this only when a tool requires OpenAI-compatible `/v1/chat/completions`.

```env
AI_CHAT_PROVIDER=openai_compatible
MODEL_PROVIDER_MODE=openai_compatible
MODEL_API_BASE_URL=http://127.0.0.1:11434/v1
MODEL_API_KEY=ollama
MODEL_NAME=deepseek-r1:8b
```

Native Ollama is still preferred because CarbonRag can preserve `message.thinking`, `keep_alive`, and `num_ctx` more directly.

## vLLM Route

Use vLLM when the machine has enough GPU memory and serves a local model through an OpenAI-compatible endpoint.

```env
AI_CHAT_PROVIDER=openai_compatible
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
AI_CHAT_PROVIDER=openai_compatible
MODEL_PROVIDER_MODE=openai_compatible
MODEL_API_BASE_URL=http://127.0.0.1:1234/v1
MODEL_API_KEY=lm-studio-local-key
MODEL_NAME=local-model
```

Profile file:

```text
.env.llm.lmstudio.example
```

## Local-Dev vs Cloud

- Local-dev: backend and Ollama are on the same machine, so `http://localhost:11434` works.
- Cloud: Netlify + VPS cannot access a user's local `localhost`; switch active provider back to `carbonrag_cloud` / `openai_compatible`, or deploy a reachable remote Ollama endpoint.

Do not test cloud behavior by pointing the VPS backend to a developer laptop's localhost. It cannot work.

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

1. Start Ollama.
2. Confirm `ollama list` includes `deepseek-r1:8b`.
3. Run `scripts/llm-ollama-smoke.ps1`.
4. Run a KnowledgeBaseWorkbench Test QA and confirm `answer_mode=llm_grounded`.
5. Run AskPage with a selected KB and confirm citations plus retrieval trace.
6. Confirm trace includes `provider=ollama` and `model=deepseek-r1:8b`.

Cloud chat API fallback is allowed for emergency comparison only. It is not the V1.6.17 local-dev default route.

If the project chooses an embedded model-loading route instead of an external local HTTP endpoint, update this document and the `.env.llm.*.example` profiles before asking other teams to reproduce it.
