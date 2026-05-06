## Purpose
Defines how CarbonRag calls model providers and manages streaming, thinking, retries, model settings, and provider overrides.

## Requirements

### Requirement: Provider runtime supports configured model access
CarbonRag SHALL route model calls through provider abstractions and user/provider configuration rather than page-level direct API access.

#### Scenario: Ask uses active provider
- **WHEN** an authenticated user sends an ask request
- **THEN** the runtime resolves the active provider before calling the model

### Requirement: Streaming and thinking events are runtime responsibilities
CarbonRag SHALL classify streaming answer chunks, thinking chunks, retry status, timeout, and provider errors inside AI runtime/provider layers.

#### Scenario: Streamed response emits typed events
- **WHEN** a provider returns streamed output
- **THEN** CarbonRag emits typed stream lifecycle events instead of exposing raw provider frames
