# Tasks

## Proposal

- [x] Create V1.4.1 OpenSpec change for optional Docling parser provider.
- [x] Confirm default parser behavior remains unchanged.

## Apply

- [x] Add optional `DoclingParserProvider`.
- [x] Add parser registry selection and fallback.
- [x] Add default `RAG_PARSER_PROVIDER=default` config.
- [x] Add optional dependency documentation.
- [x] Add tests for missing Docling, default selection, docling fallback, metadata, RAG compatibility, and `/ask` regression.
- [x] Run `openspec validate optional-docling-parser-provider --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build.
- [x] Commit locally without push or PR.
