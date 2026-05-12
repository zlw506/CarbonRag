# Tasks

- [x] Add native Ollama client/provider support for `/api/chat`, streaming, `think`, `num_ctx`, and `keep_alive`.
- [x] Dispatch provider factory by provider type, with `ollama` defaulting to `deepseek-r1:8b`.
- [x] Route RAG Test QA and `/rag/answer` through the current active provider or local provider override.
- [x] Add SettingsPage one-click Ollama / DeepSeek-R1 8B provider template.
- [x] Add Ollama local env profile, smoke scripts, architecture doc, and V1.6.17 plan.
- [x] Run live Ollama smoke on a machine where `deepseek-r1:8b` is loaded.
- [ ] Run full Qingmu RAG E2E with Milvus Standalone + BGE-M3 + Ollama generation.
