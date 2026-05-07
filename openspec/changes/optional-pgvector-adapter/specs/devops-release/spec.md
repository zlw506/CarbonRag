## MODIFIED Requirements

### Requirement: Runtime vector backends are optional
CarbonRag SHALL keep vector backend configuration optional for local development and private deployments.

#### Scenario: Default local development starts without pgvector
- **WHEN** local development uses the default environment template
- **THEN** `RAG_VECTOR_BACKEND=current` is configured
- **AND** no Postgres or pgvector connection is required

#### Scenario: Private deployment enables pgvector manually
- **WHEN** an operator sets `RAG_VECTOR_BACKEND=pgvector`
- **THEN** CarbonRag provides a manual SQL bootstrap file for creating the pgvector extension and `rag_embeddings` table
