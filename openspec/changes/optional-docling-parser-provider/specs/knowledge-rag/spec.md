## MODIFIED Requirements

### Requirement: Parser providers are additive
CarbonRag SHALL define a parser provider boundary that can wrap existing lightweight parsing and later support optional Docling and MinerU providers without changing knowledge task ownership rules.

#### Scenario: Default parser remains the default
- **WHEN** no parser provider override is configured
- **THEN** CarbonRag uses `DefaultParserProvider`

#### Scenario: Docling is unavailable
- **WHEN** `DoclingParserProvider` is constructed without Docling installed
- **THEN** the application still starts
- **AND** the provider reports unavailable support without raising an import error

#### Scenario: Docling is configured but unavailable
- **WHEN** parser selection requests Docling but Docling is not available
- **THEN** CarbonRag falls back to `DefaultParserProvider`
- **AND** the parsed document metadata records the fallback reason

#### Scenario: Docling parse metadata is normalized
- **WHEN** Docling parsing is available and succeeds
- **THEN** CarbonRag returns a unified `ParsedDocument` with metadata including `parser_name=docling`, parser availability, parser version when available, parse success, and parse error

#### Scenario: Existing flows remain compatible
- **WHEN** optional Docling support is added
- **THEN** retrieval-only, RAG Lab, and `/ask` default behavior continue to work without requiring Docling
