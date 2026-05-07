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

### Requirement: Enterprise RAG contracts are stable before providers
CarbonRag SHALL define reusable contracts for parsed documents, document blocks, chunk records, embedding records, citation references, and retrieval traces before adding heavy external parser, vector, graph, or workflow dependencies.

#### Scenario: Existing chunks enter the unified contract
- **WHEN** existing public or private BM25 chunks are returned through the RAG engine
- **THEN** CarbonRag can map them to a stable chunk record and citation reference shape without changing ask/session behavior

#### Scenario: Retrieval traces are returned for debugging
- **WHEN** retrieval-only data is requested
- **THEN** CarbonRag records trace metadata such as strategy, active retrieval path, latency, and fallback reason

### Requirement: Parser providers are additive
CarbonRag SHALL define a parser provider boundary that can wrap existing lightweight parsing and later support Docling and MinerU without changing knowledge task ownership rules.

#### Scenario: Lightweight parser handles supported file
- **WHEN** a supported local text-like document is parsed through the provider boundary
- **THEN** CarbonRag returns parsed text, document blocks, parser metadata, and a quality score

### Requirement: Vector store adapters are disabled-safe
CarbonRag SHALL define a vector store adapter boundary for upsert, search, delete, and healthcheck operations while keeping disabled vector storage safe by default.

#### Scenario: Vector store is not configured
- **WHEN** vector indexing or vector search is requested without an enabled vector backend
- **THEN** CarbonRag reports disabled health and preserves BM25 fallback behavior

### Requirement: Hybrid retrieval strategies are explicit
CarbonRag SHALL name retrieval strategies separately from retrieval implementations so later dense, sparse, graph, and citation-first retrieval can be composed safely.

#### Scenario: Strategy is planned before execution
- **WHEN** the RAG engine prepares retrieval-only output
- **THEN** CarbonRag records the intended strategy and active retrieval path in metadata

### Requirement: Graph and workflow skeletons are dependency-light
CarbonRag SHALL define graph index and workflow checkpoint skeletons without requiring Neo4j, LangGraph, or external workflow services in V1.3.x.

#### Scenario: Graph indexing is unavailable
- **WHEN** graph candidates are requested before a graph backend exists
- **THEN** CarbonRag returns an unavailable graph status and does not fail retrieval
