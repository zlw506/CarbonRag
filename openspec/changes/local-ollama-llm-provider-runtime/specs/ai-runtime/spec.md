## ADDED Requirements

### Requirement: Ollama native chat provider
CarbonRag SHALL support a local Ollama chat provider that calls Ollama's native chat API and preserves thinking metadata.

#### Scenario: Ollama chat is selected
- **WHEN** the active provider type is `ollama`
- **THEN** CarbonRag calls the Ollama native `/api/chat` endpoint
- **AND** the request includes the configured model, messages, streaming flag, `num_ctx`, `keep_alive`, and `think` options where configured
- **AND** response metadata records the Ollama provider and model.

#### Scenario: Ollama thinking is streamed
- **WHEN** Ollama returns `message.thinking`
- **THEN** CarbonRag emits or records it as thinking metadata instead of dropping it.

### Requirement: Provider factory dispatches by provider type
CarbonRag SHALL select the chat provider implementation from runtime or user provider configuration.

#### Scenario: Local Ollama provider is active
- **WHEN** provider type is `ollama`
- **THEN** CarbonRag builds an Ollama provider without requiring an API key.

#### Scenario: OpenAI-compatible Ollama endpoint is active
- **WHEN** provider type is `openai_compatible` and base URL is an Ollama `/v1` endpoint
- **THEN** CarbonRag uses the OpenAI-compatible provider path.
