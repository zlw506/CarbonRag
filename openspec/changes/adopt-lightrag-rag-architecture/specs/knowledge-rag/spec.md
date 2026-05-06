## ADDED Requirements

### Requirement: RAG engine separates retrieval layers
CarbonRag SHALL define an M5 RAG engine boundary that separates source documents, document processing status, text chunks, vector chunk retrieval, optional entity/relation graph candidates, and evidence references.

#### Scenario: Knowledge item enters the RAG engine
- **WHEN** a supported knowledge item is indexed by the RAG engine
- **THEN** CarbonRag records retrieval-ready chunk data and document status without bypassing existing knowledge item ownership and visibility rules

#### Scenario: Existing retrieval remains available
- **WHEN** the experimental RAG engine is unavailable or disabled
- **THEN** CarbonRag continues to use the existing public, private, and mixed BM25 retrieval paths

### Requirement: RAG query parameters define retrieval mode
CarbonRag SHALL use an internal query parameter model for RAG retrieval mode, top-k limits, chunk limits, token budgets, rerank toggle, reference inclusion, and retrieval-only execution.

#### Scenario: Naive query mode is requested
- **WHEN** a retrieval request uses `naive` mode
- **THEN** CarbonRag retrieves text chunks through the configured vector-capable path or records a fallback to the existing BM25 path

#### Scenario: Mix query mode is requested
- **WHEN** a retrieval request uses `mix` mode
- **THEN** CarbonRag combines vector chunk candidates with any available graph candidates and returns merged evidence references

### Requirement: Retrieval data is structured before answer generation
CarbonRag SHALL expose structured retrieval data before LLM answer generation, including retrieved chunks, references, scores, source types, retrieval mode, and fallback metadata.

#### Scenario: Retrieval-only inspection
- **WHEN** the runtime requests retrieval-only data for a user question
- **THEN** CarbonRag returns structured evidence without requiring a chat completion call

#### Scenario: Ask mode consumes retrieval data
- **WHEN** ask mode uses RAG evidence to build context
- **THEN** CarbonRag passes formatted evidence derived from structured retrieval data rather than raw storage rows

### Requirement: Graph evidence is optional in the minimal skeleton
CarbonRag SHALL allow entity and relation graph evidence to be absent in V1.3.0 while preserving a stable result shape for later graph extraction work.

#### Scenario: Mix mode runs without graph index
- **WHEN** `mix` mode runs before entity/relation graph extraction is available
- **THEN** CarbonRag returns vector or fallback chunks and marks graph evidence as unavailable instead of failing the request

### Requirement: LightRAG source reuse preserves licensing
CarbonRag SHALL preserve MIT license notices and source attribution if apply-stage work copies or adapts substantial source code from HKUDS/LightRAG.

#### Scenario: LightRAG code is vendored or adapted
- **WHEN** a PR includes substantial code copied or adapted from HKUDS/LightRAG
- **THEN** the PR includes the required license notice and documents the adapted source scope
