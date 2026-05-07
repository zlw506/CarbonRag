## MODIFIED Requirements

### Requirement: Parser providers are additive
CarbonRag SHALL define a parser provider boundary that can wrap existing lightweight parsing and later support optional Docling and MinerU providers without changing knowledge task ownership rules.

#### Scenario: Default parser remains the default
- **WHEN** no parser provider override is configured
- **THEN** CarbonRag uses `DefaultParserProvider`

#### Scenario: MinerU is disabled by default
- **WHEN** no MinerU-specific environment variables are configured
- **THEN** CarbonRag keeps MinerU disabled and starts without importing MinerU

#### Scenario: MinerU is unavailable
- **WHEN** `MinerUParserProvider` is constructed without MinerU installed
- **THEN** the application still starts
- **AND** the provider reports unavailable support without raising an import error

#### Scenario: MinerU fallback is configured but unavailable
- **WHEN** parser selection reaches MinerU in the fallback chain but MinerU is disabled, unavailable, unsupported, or fails
- **THEN** CarbonRag falls back to `DefaultParserProvider`
- **AND** the parsed document metadata records `parser_chain` and fallback reason

#### Scenario: MinerU parse metadata is normalized
- **WHEN** MinerU parsing is enabled, available, and succeeds
- **THEN** CarbonRag returns a unified `ParsedDocument` with metadata including `parser_name=mineru`, parser availability, parse success, parse error, fallback reason, and output format

#### Scenario: Existing flows remain compatible
- **WHEN** optional MinerU fallback support is added
- **THEN** retrieval-only, RAG Lab, and `/ask` default behavior continue to work without requiring MinerU
