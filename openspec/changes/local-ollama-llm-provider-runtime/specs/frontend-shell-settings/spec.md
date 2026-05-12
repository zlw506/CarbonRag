## ADDED Requirements

### Requirement: Settings page exposes Ollama DeepSeek template
CarbonRag SHALL provide a user-facing shortcut for configuring local Ollama DeepSeek-R1 8B.

#### Scenario: User fills local Ollama provider
- **WHEN** a user clicks the Ollama / DeepSeek-R1 8B template
- **THEN** the provider editor is filled with `provider_type=ollama`, `base_url=http://localhost:11434`, `model_name=deepseek-r1:8b`, and no API key.

#### Scenario: Local model list is refreshed
- **WHEN** the provider type is `ollama`
- **THEN** the settings page labels model discovery as local Ollama model refresh.
