## MODIFIED Requirements

### Requirement: Retrieval data is structured before answer generation
CarbonRag SHALL expose structured retrieval data before LLM answer generation, including retrieved chunks, references, scores, source types, retrieval mode, fallback metadata, observable counts, and retrieval latency.

#### Scenario: Retrieval-only inspection
- **WHEN** the runtime requests retrieval-only data for a user question
- **THEN** CarbonRag returns structured evidence without requiring a chat completion call
- **AND** the response metadata includes the effective retriever mode, requested top-k, returned count, fallback state, fallback reason, latency, and available public/private returned chunk counts

#### Scenario: Retrieval-only request returns no hits
- **WHEN** the retrieval-only API completes successfully with no matching chunks
- **THEN** CarbonRag returns `chunks` and `references` as empty lists
- **AND** the response metadata records `returned_count` as `0` without failing the request

#### Scenario: Retrieval-only request is invalid
- **WHEN** the retrieval-only API receives a blank query or invalid top-k
- **THEN** CarbonRag returns a clear validation error without invoking answer generation

#### Scenario: Retrieval-only execution fails unexpectedly
- **WHEN** retrieval-only execution raises an unexpected exception
- **THEN** CarbonRag returns a structured backend error detail instead of an empty 500 response

#### Scenario: Ask mode consumes retrieval data
- **WHEN** ask mode uses RAG evidence to build context
- **THEN** CarbonRag passes formatted evidence derived from structured retrieval data rather than raw storage rows
