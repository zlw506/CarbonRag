## ADDED Requirements

### Requirement: RAG generation uses active chat provider
CarbonRag SHALL use the currently resolved chat provider for RAG grounded answer generation.

#### Scenario: Workbench Test QA uses local Ollama
- **WHEN** a user runs KnowledgeBaseWorkbench Test QA with active provider `ollama`
- **THEN** `/rag/test-qa` uses the Ollama provider to generate the grounded answer
- **AND** the response reports provider and model metadata.

#### Scenario: RAG answer uses local Ollama
- **WHEN** `/rag/answer` is called with an active Ollama provider or request provider override
- **THEN** the grounded answer is generated through Ollama
- **AND** retrieval trace remains visible.
