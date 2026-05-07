## Scope

This change is a parser adapter only. It does not route the existing knowledge ingest task through Docling and does not require Docling during local development or CI.

## Dependency Strategy

- Use try-import fallback inside `DoclingParserProvider`.
- Add `backend/requirements-optional.txt` with the optional Docling package name for manual installation.
- Keep `RAG_PARSER_PROVIDER=default` as the default configuration.

## Registry Strategy

- `ParserRegistry` owns provider selection.
- If `RAG_PARSER_PROVIDER=docling` and Docling is importable, Docling is tried first.
- If Docling is unavailable or parsing fails, the registry falls back to `DefaultParserProvider`.
- Fallback metadata is added to the returned `ParsedDocument`.

## Non-Goals

- No MinerU, OCR fallback, async task system, ingestion rewrite, or mandatory dependency.
