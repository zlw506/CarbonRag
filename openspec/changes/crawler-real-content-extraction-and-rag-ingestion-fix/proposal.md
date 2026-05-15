# Change: crawler-real-content-extraction-and-rag-ingestion-fix

## Why

V1.7.2 made crawler candidates publishable to the RAG-Pro KB, but gov.cn pages can still degrade into raw HTML artifacts. That makes previews empty, quality scores misleading, and RAG publish unreliable.

## What Changes

- Add a gov.cn policy HTML extractor for title, document number, publication date, source, and正文.
- Write audited crawler artifacts: `raw.html`, `cleaned.txt`, `document.md`, and `extraction.json`.
- Expose admin artifact diagnostics and make crawler preview prefer those artifacts.
- Split extraction quality from topic relevance and block empty/low-quality RAG publish.
- Use crawler-specific long frontend timeouts for dry-run, run, and publish-to-RAG.

## Out Of Scope

- No new crawler source expansion.
- No scheduled crawler runtime.
- No Crawl4AI/Crawlab runtime dependency.
- No UI redesign beyond reliability indicators.
