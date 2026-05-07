# Tasks

## Proposal

- [x] Create V1.4.0 OpenSpec change for parser provider boundary.
- [x] Confirm scope is provider wrapping only.

## Apply

- [x] Add `DefaultParserProvider` around current lightweight parsing.
- [x] Keep `ParserProvider` and `LightweightParserProvider` compatibility.
- [x] Add parser metadata for parser name/version/source/success/error.
- [x] Add simple 0-1 parsing quality score.
- [x] Add tests for supported files, ParsedDocument output, non-empty blocks, score range, parse error metadata, ingest compatibility, and `/ask` regression.
- [x] Run `openspec validate parser-provider-boundary --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build for RAG Lab compatibility.
