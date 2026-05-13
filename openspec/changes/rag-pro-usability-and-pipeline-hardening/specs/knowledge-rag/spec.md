## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL expose a KnowledgeBase -> Document -> Chunk -> Retrieval -> Answer spine as the primary RAG path.

#### Scenario: Document pipeline can be run as one acceptance action

- **WHEN** a user triggers one-click ingestion for a document in a knowledge base
- **THEN** CarbonRag runs parse, chunk, index, search smoke, and optional eval smoke in order
- **AND** the response includes parse status, chunk status, index status, chunk count, indexed chunk count, vector runtime, degradation state, smoke results, failed stage, and warnings
- **AND** execution stops at the first failed stage instead of hiding the failure

#### Scenario: Batch pipeline summarizes multiple documents

- **WHEN** a user triggers batch one-click ingestion for a knowledge base
- **THEN** CarbonRag processes unindexed or failed documents by default
- **AND** may limit the batch to explicit `doc_ids`
- **AND** returns total, succeeded, failed, and per-document pipeline results

#### Scenario: Legacy retrieval is not the acceptance path

- **WHEN** a non-admin user calls `/api/v1/rag/retrieve`
- **THEN** access is denied
- **AND** formal RAG acceptance remains `/rag/search`, `/rag/answer`, `/rag/test-qa`, `/rag/eval/run`, KnowledgeBaseWorkbench, and AskPage

#### Scenario: AskPage exposes RAG proof

- **WHEN** AskPage renders an assistant answer with RAG metadata
- **THEN** it exposes the selected knowledge base, retrieval mode, provider, model, vector runtime, degradation state, hit counts, rerank status, citation count, selected chunks, and warnings
- **AND** degraded or incomplete RAG states are visibly marked as risk instead of appearing successful
