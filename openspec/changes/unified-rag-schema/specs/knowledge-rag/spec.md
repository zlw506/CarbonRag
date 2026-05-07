## MODIFIED Requirements

### Requirement: Enterprise RAG contracts are stable before providers
CarbonRag SHALL define reusable Pydantic contracts for parsed documents, document blocks, chunk records, embedding records, citation references, and retrieval traces before adding heavy external parser, vector, graph, or workflow dependencies.

#### Scenario: Parsed documents use block-level structure
- **WHEN** a document is parsed through the RAG contract boundary
- **THEN** CarbonRag can represent document id, source URI, source type, title, ordered blocks, and metadata
- **AND** each document block can represent block id, document id, block type, text, page, section, order index, and metadata

#### Scenario: Existing chunks enter the unified contract
- **WHEN** existing public or private chunks are returned through current retrieval
- **THEN** CarbonRag can adapt them into `ChunkRecord` objects with chunk id, document id, text, source type, title, page, section, block ids, and metadata without changing ask/session behavior

#### Scenario: Existing references enter the unified contract
- **WHEN** retrieval-only evidence references are produced
- **THEN** CarbonRag can adapt them into `CitationRef` objects with citation id, document id, chunk id, title, page, section, source URI, quote, and metadata

#### Scenario: Retrieval traces are returned for debugging
- **WHEN** retrieval-only data is requested
- **THEN** CarbonRag records trace metadata such as trace id, query, retriever mode, requested top-k, returned count, fallback status, fallback reason, latency, returned chunk ids, citation refs, and provider metadata

#### Scenario: Retrieval-only response remains compatible
- **WHEN** unified contract data is added internally
- **THEN** the retrieval-only API still returns the existing `chunks`, `references`, and `metadata` fields and only adds trace or metadata detail
