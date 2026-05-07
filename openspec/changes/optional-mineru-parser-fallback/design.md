## Scope

This change is a parser adapter boundary only. It does not route existing knowledge ingest through MinerU and does not require MinerU during local development or CI.

## Dependency Strategy

- MinerU is detected lazily with optional imports.
- `RAG_ENABLE_MINERU=false` remains the default.
- Optional requirements document the manual MinerU stack without installing it by default.
- If MinerU is missing, disabled, unsupported, or fails, CarbonRag continues running and falls back to the default parser.

## Registry Strategy

- `ParserRegistry` continues to use `DefaultParserProvider` when `RAG_PARSER_PROVIDER=default`.
- When optional parser routing is requested, the registry evaluates the configured `RAG_PARSER_FALLBACK_CHAIN`.
- Docling may be attempted before MinerU for PDFs when configured.
- MinerU is attempted only when explicitly enabled and supported.
- Returned `ParsedDocument.metadata` records a `parser_chain` such as `["docling:failed", "mineru:unavailable", "default:success"]`.

## Non-Goals

- No full MinerU deployment.
- No OCR fallback runtime.
- No Docling removal.
- No knowledge ingest rewrite.
- No RAG engine, retrieval-only API, RAG Lab, or `/ask` behavior changes.
