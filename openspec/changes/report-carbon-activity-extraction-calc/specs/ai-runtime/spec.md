## ADDED Requirements

### Requirement: Ask can run report carbon extraction tools
CarbonRag SHALL allow Ask mode to invoke a controlled report carbon extraction and calculation tool when a user asks carbon-calculation questions about selected uploaded reports.

#### Scenario: User asks to calculate emissions from an uploaded report
- **WHEN** the Ask request includes selected parsed uploaded files
- **AND** the user asks for carbon factor quantities or carbon emission calculation from the report
- **THEN** AI Runtime invokes the report carbon extraction tool after retrieval
- **AND** the model context includes extracted activity quantities, calculation result, warnings, and source chunk citations

