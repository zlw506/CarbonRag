## Why
Users upload enterprise reports that contain carbon-related activity data across prose, tables, OCR text, and parsed file chunks. CarbonRag currently can retrieve uploaded file snippets and can calculate emissions from structured activity inputs, but the Ask workflow does not bridge those two capabilities.

## What Changes
- Add a session report carbon extraction tool that reads selected parsed uploads from the current session.
- Extract carbon activity quantities from report chunks and map them to supported CarbonRag activity items.
- Calculate emissions with the existing carbon factor registry and carbon calculation engine.
- Inject extraction and calculation evidence into Ask context so the model can answer with extracted quantities, factors, totals, warnings, and citations.

## Scope
- Backend AI Runtime, carbon calculation, and uploaded-file knowledge chunks.
- No new front-end page in this change.
- No new OCR engine; the tool consumes the parsed text/table/OCR chunks produced by the existing document parsing pipeline.

