## ADDED Requirements

### Requirement: Experimental RAG configuration is safe by default
CarbonRag SHALL keep experimental vector, graph, and rerank RAG features disabled or fallback-safe unless explicitly configured through tracked environment templates or documented runtime settings.

#### Scenario: Optional RAG settings are missing
- **WHEN** local or cloud runtime starts without experimental RAG provider settings
- **THEN** CarbonRag starts successfully and preserves existing BM25 retrieval behavior

#### Scenario: Optional RAG backend fails to initialize
- **WHEN** an optional vector, graph, embedding, or rerank backend fails to initialize
- **THEN** CarbonRag records the unavailable backend state and keeps existing retrieval paths usable

### Requirement: RAG environment changes are documented
CarbonRag SHALL update tracked env templates and deployment/bootstrap docs when V1.3.0 introduces optional RAG engine configuration.

#### Scenario: Contributor configures experimental RAG locally
- **WHEN** a contributor reads the tracked templates and development docs
- **THEN** the contributor can identify which RAG settings are optional, which are required for vector retrieval, and how to return to fallback mode
