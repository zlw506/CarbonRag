## Why

CarbonRag already ingests uploaded and shared knowledge files through a lightweight parser in `app.knowledge.parsers`. V1.4.0 should introduce a parser-provider boundary so future Docling and MinerU integrations can plug in behind a stable interface, while the current upload, ingest, retrieval-only, RAG Lab, and `/ask` behavior stay unchanged.

## What Changes

- Extend the existing `app.rag.parser` provider boundary instead of duplicating parser abstractions.
- Add `DefaultParserProvider` that wraps the current lightweight parser capability.
- Keep `LightweightParserProvider` as a compatibility alias/subclass for existing tests and imports.
- Add parse metadata for parser name, parser version, source file, parse success, and parse error.
- Add simple parser quality scoring based on text presence, title/heading detection, page metadata, and parse failure.
- Add tests for supported file detection, parsed document blocks, scoring, parse failure metadata, existing ingest flow, and `/ask` regression.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add a default parser provider boundary around current lightweight parsing.

## Impact

- Affected modules: M5 primary.
- Apply-stage areas: `backend/app/rag/parser.py`, RAG exports, parser tests, and existing knowledge ingestion tests.
- No Docling, MinerU, OCR, heavy dependency, async task system, RAG engine rewrite, retrieval-only API change, or `/ask` behavior change is proposed.
