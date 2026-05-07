## Why

CarbonRag now has a parser-provider boundary and an optional Docling adapter. V1.4.2 should reserve a MinerU fallback adapter for complex PDF parsing without making MinerU, OCR, or its runtime stack mandatory for local development, CI, or default application startup.

## What Changes

- Add `MinerUParserProvider` behind the existing `ParserProvider` contract.
- Keep MinerU disabled by default through `RAG_ENABLE_MINERU=false`.
- Add `RAG_PARSER_FALLBACK_CHAIN=docling,mineru,default` so future parser routing can record an explicit fallback path.
- Extend `ParserRegistry` to record `parser_chain` metadata and fall back safely when Docling or MinerU is unavailable or fails.
- Document MinerU as a manual optional parser stack rather than a required dependency.
- Add tests that mock MinerU availability and conversion behavior instead of requiring a real MinerU installation.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add an optional MinerU parser fallback reservation and parser-chain metadata under the existing parser provider boundary.

## Impact

- Affected modules: M5 primary, M7 env template only.
- Apply-stage areas: `backend/app/rag/parser.py`, `backend/app/rag/__init__.py`, `backend/app/core/config.py`, `.env.example`, optional requirements, OpenSpec change files, and parser tests.
- No default parser change, Docling removal, ingest rewrite, RAG Lab change, retrieval-only change, `/ask` behavior change, OCR deployment, async task system, or mandatory MinerU dependency is proposed.
