## Why

CarbonRag V1.4.0 added a parser-provider boundary around the current lightweight parser. V1.4.1 should add a Docling adapter behind that boundary without making Docling a required dependency or changing the default parser behavior.

## What Changes

- Add `DoclingParserProvider` with safe import fallback when Docling is not installed.
- Add `ParserRegistry` that chooses `DefaultParserProvider` by default and uses Docling only when configured.
- Add fallback behavior from Docling to default parsing with fallback metadata.
- Add optional dependency documentation through `backend/requirements-optional.txt` and `.env.example` configuration.
- Add tests that mock provider availability instead of requiring a real Docling install.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add an optional Docling parser provider and registry-based parser selection.

## Impact

- Affected modules: M5 primary.
- Apply-stage areas: `backend/app/rag/parser.py`, `backend/app/core/config.py`, `.env.example`, optional requirements, and parser tests.
- No DefaultParserProvider removal, MinerU, OCR, ingest rewrite, RAG Lab change, retrieval-only change, `/ask` behavior change, or mandatory Docling dependency is proposed.
