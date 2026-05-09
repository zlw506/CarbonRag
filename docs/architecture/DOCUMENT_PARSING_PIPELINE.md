# Document Parsing Pipeline

V1.5.1 uses a Docling-first parser pipeline with safe local fallbacks.

## Parser Order

1. `DoclingParserProvider` when available and supported.
2. Lightweight fallback parsers for text-like and Office Open XML files.
3. Explicit failure for unsupported, unreadable, image-only, or OCR-required files when OCR support is unavailable.

## Supported Inputs

Allowed upload extensions:

- `pdf`
- `docx`
- `xlsx`
- `csv`
- `txt`
- `md`
- `html`
- `pptx`
- `png`
- `jpg`
- `jpeg`

Rejected classes:

- executables
- scripts
- archives
- macro-enabled Office files
- legacy binary Office files such as `.doc`

## Persisted Results

`file_parse_results` stores:

- extracted markdown/text
- optional JSON path/payload
- summary
- chunk count
- parser name/version
- metadata JSON

`knowledge_chunks.metadata_json` stores file locator hints so retrieval and citations can preserve page, sheet, slide, or section references.

## OCR Policy

PDFs are not blindly converted to images. Text PDFs use text extraction first. Images and scanned PDFs require Docling/OCR support. If OCR is unavailable, the file fails clearly with `parse_failed / ocr_unavailable` style messaging rather than pretending the content was read.
