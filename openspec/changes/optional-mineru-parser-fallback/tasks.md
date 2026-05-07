# Tasks

## Proposal

- [x] Create V1.4.2 OpenSpec change for optional MinerU fallback reservation.
- [x] Confirm ParserProvider, DefaultParserProvider, and DoclingParserProvider already exist.

## Apply

- [x] Add `MinerUParserProvider` with safe optional availability checks.
- [x] Add disabled-by-default MinerU settings and fallback-chain configuration.
- [x] Extend `ParserRegistry` to record `parser_chain` and fall back through Docling, MinerU, and default safely.
- [x] Export the MinerU provider without changing existing parser imports.
- [x] Document MinerU as an optional manual dependency.
- [x] Add tests for missing MinerU, disabled MinerU, unavailable fallback, parser-chain metadata, metadata serializability, RAG compatibility, and `/ask` regression.
- [x] Run `openspec validate optional-mineru-parser-fallback --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build.
- [x] Commit locally without push or PR.
