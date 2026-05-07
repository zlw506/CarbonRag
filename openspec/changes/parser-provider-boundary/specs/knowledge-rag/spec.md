## MODIFIED Requirements

### Requirement: Parser providers are additive
CarbonRag SHALL define a parser provider boundary that can wrap existing lightweight parsing and later support Docling and MinerU without changing knowledge task ownership rules.

#### Scenario: Default parser supports current file types
- **WHEN** a supported current knowledge file type such as markdown, text, CSV, Excel, DOCX, or text-based PDF is checked
- **THEN** `DefaultParserProvider.supports()` returns true without requiring Docling, MinerU, or OCR

#### Scenario: Default parser returns parsed document contract
- **WHEN** `DefaultParserProvider` parses a supported text-like document
- **THEN** CarbonRag returns a `ParsedDocument` with source URI, title, text, document blocks, parser metadata, and a quality score between 0 and 1

#### Scenario: Parser failure is observable
- **WHEN** default parsing fails or receives an unsupported file
- **THEN** CarbonRag returns a failed `ParsedDocument` for provider-level inspection with `parse_success=false`, `parse_error`, and quality score `0`

#### Scenario: Existing knowledge ingestion stays compatible
- **WHEN** uploaded knowledge files are ingested through the current task runner
- **THEN** CarbonRag preserves the existing parse, chunk, store, and failure behavior
