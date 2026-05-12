# Design

## Runtime Shape

CarbonRag uses its existing `OpenAICompatibleChatProvider` as the common adapter for local model servers.

Supported profiles:

- Ollama OpenAI-compatible endpoint: `http://127.0.0.1:11434/v1`
- vLLM OpenAI-compatible endpoint: `http://127.0.0.1:8001/v1`
- LM Studio OpenAI-compatible endpoint: `http://127.0.0.1:1234/v1`

The Settings page can still use the native `Ollama` provider type with `http://localhost:11434/api`. The `.env` default uses the OpenAI-compatible route because it is shared by Ollama, vLLM, and LM Studio.

## Model Placement

Chat model packages are local runtime assets:

```text
data/outputs/models/LLM/<model-name>/
```

They are not source code and must stay ignored by Git.

Retrieval assets remain:

```text
data/outputs/models/BAAI/bge-m3
data/outputs/models/BAAI/bge-reranker-v2-m3
```

## Smoke

The smoke script checks `/models` opportunistically and requires `/chat/completions` to return a non-empty message. This catches the common failure mode where the server is running but the model is not loaded.

