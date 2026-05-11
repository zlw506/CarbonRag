## ADDED Requirements

### Requirement: Parsed upload chunks support report activity extraction
CarbonRag SHALL reuse parsed upload chunks as the evidence source for report carbon activity extraction.

#### Scenario: Upload parser produces text, table, or OCR chunks
- **WHEN** a supported file parser produces chunks from report text, table, or OCR-derived content
- **THEN** the report carbon extraction tool can inspect those chunks
- **AND** preserves page, sheet, slide, section, file id, and chunk id metadata in extracted activity evidence

