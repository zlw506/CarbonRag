## ADDED Requirements

### Requirement: AI Runtime supports local OpenAI-compatible chat LLM profiles

CarbonRag SHALL support local open-source chat model runtimes through OpenAI-compatible endpoints without requiring model weights to be committed to the repository.

#### Scenario: Developer uses Ollama DeepSeek locally

- **WHEN** `MODEL_API_BASE_URL=http://127.0.0.1:11434/v1` and `MODEL_NAME=deepseek-r1:8b`
- **THEN** CarbonRag uses the existing OpenAI-compatible chat provider to call the local chat model.

#### Scenario: Local chat smoke is run

- **WHEN** `scripts/llm-smoke-openai-compatible.ps1` is executed with a loaded local model
- **THEN** the script verifies `/v1/chat/completions` returns a non-empty answer.

#### Scenario: Offline chat model package is used

- **WHEN** a developer receives a local chat model package from #1
- **THEN** the package is extracted under `data/outputs/models/LLM/<model-name>/` and remains ignored by Git.

