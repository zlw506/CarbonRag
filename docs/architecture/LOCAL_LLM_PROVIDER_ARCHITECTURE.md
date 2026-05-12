# Local Ollama LLM Provider Architecture

V1.6.17 makes Ollama a first-class chat provider for local RAG development.

## Runtime Boundary

- Local-dev: backend and Ollama run on the same machine, and CarbonRag calls `http://localhost:11434`.
- Cloud: Netlify + VPS cannot access a user's local `localhost`; use cloud provider settings or deploy a reachable remote Ollama endpoint.
- Model weights are never committed. Offline chat model packages must be provided out of band by #1 if needed.

## Provider Routes

Primary route:

```text
provider_type=ollama
base_url=http://localhost:11434
model_name=deepseek-r1:8b
POST /api/chat
```

Compatibility route:

```text
provider_type=openai_compatible
base_url=http://localhost:11434/v1
api_key=ollama
model_name=deepseek-r1:8b
POST /v1/chat/completions
```

Native Ollama is preferred because it supports `think`, `keep_alive`, and `options.num_ctx`. CarbonRag preserves `message.thinking` as thinking trace instead of dropping it.

## RAG Generation

The retrieval stack stays unchanged:

```text
BGE-M3 -> Milvus Docker -> hybrid/RRF -> bge-reranker
```

Only the final grounded generation step changes:

```text
retrieved chunks -> grounded prompt -> Ollama deepseek-r1:8b -> answer + citations + trace
```

## Required Local Smoke

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/llm-ollama-smoke.ps1
```

The smoke verifies `/api/tags` and `/api/chat` for `deepseek-r1:8b`.
