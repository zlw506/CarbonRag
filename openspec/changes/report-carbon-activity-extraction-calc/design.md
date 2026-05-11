## Design

### Pipeline
1. Ask receives a carbon/report question with selected uploaded files.
2. AI Runtime runs normal RAG retrieval and then `report_carbon_extract_calc` when the turn looks like report carbon extraction or carbon calculation.
3. The tool reads selected `private_upload` chunks from `KnowledgeService`.
4. A deterministic extractor scans chunk text for carbon activity rows and quantities.
5. Extracted items are converted into `CarbonActivityItem` records with evidence metadata.
6. `CarbonService.calculate` uses the existing factor registry, runtime factor DB, and seed fallback.
7. The tool returns extracted items, factor snapshots, formula traces, calculation result, warnings, and private-upload citations.

### Multimodal Boundary
This change does not add a new vision model. It treats Docling/fallback parser outputs as the shared representation for text, table, and OCR-derived image content. Parsed chunk metadata such as page number, sheet name, slide number, and section title is preserved as evidence.

### Matching Rules
The first extractor covers common enterprise activity aliases:
- purchased electricity: `用电量`, `外购电力`, `电量`, `kWh`
- natural gas: `天然气`, `燃气`, `m3`, `立方米`
- diesel: `柴油`, `L`, `升`
- gasoline: `汽油`, `L`, `升`
- LPG: `液化石油气`, `LPG`, `kg`
- coal: `煤`, `烟煤`, `无烟煤`, `t`, `吨`

The extractor is conservative: it returns warnings when evidence is ambiguous, no selected uploads exist, no supported quantities are found, or calculation fails.

### Persistence
When extracted activity items exist, the tool calls `CarbonService.calculate` with the current session id so the calculation can be reused by reports. Empty extraction does not create a calculation.

