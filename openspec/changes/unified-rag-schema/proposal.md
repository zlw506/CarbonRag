## Why

CarbonRag V1.3 already returns structured RAG chunks, references, and metadata, and the enterprise roadmap calls for one data contract connecting parsing, chunking, indexing, retrieval, and citation display. The current RAG contract file contains early versions of these models, but it does not yet fully align with the V1.3.2 contract names and adapter requirements.

## What Changes

- Extend the existing `app.rag.contracts` Pydantic models instead of creating duplicate schema classes.
- Align `ParsedDocument`, `DocumentBlock`, `ChunkRecord`, `EmbeddingRecord`, `CitationRef`, and `RetrievalTrace` with the V1.3.2 field set while keeping legacy helper fields compatible.
- Add adapter helpers for existing public/private `RetrievedChunk`, RAG evidence chunks, evidence references, and retrieval results.
- Start attaching a richer internal `RetrievalTrace` to retrieval-only metadata without removing existing `chunks`, `references`, or `metadata` fields.
- Add tests that prove public/private chunks and references map into the unified contract, and that retrieval-only and `/ask` behavior remain compatible.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add a unified RAG data contract and adapter layer for existing retrieval outputs.

## Impact

- Affected modules: M5 primary.
- Apply-stage areas: `backend/app/rag/contracts.py`, `backend/app/rag/adapters.py`, `backend/app/rag/service.py`, `backend/tests/**`, and narrow frontend type tolerance if required by metadata trace shape.
- No engine rewrite, vector backend change, parser integration, graph retrieval, Docling, MinerU, pgvector, Qdrant, or API response removal is proposed.
