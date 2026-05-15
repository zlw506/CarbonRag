# Change: crawler-source-registry-and-rag-quality-loop

## Why

V1.7.0 connected crawler candidates to the RAG-Pro KB quick pipeline, but the crawler still behaves like a fixed internal tool. V1.7.2 adds a managed official source registry, dry-run preview, candidate quality scoring, and visible RAG publish status so the crawler can serve as a controlled auto-update baseline.

## What Changes

- Add admin-only Source CRUD and recommended source import.
- Add dry-run preview for candidate discovery without writing DB records or RAG documents.
- Add candidate quality score and block low-quality candidate RAG publish.
- Expand recommended dual-carbon official sources.
- Expose source quality, RAG publish status, and dry-run preview in the admin UI.

## Out Of Scope

- No Crawlab runtime.
- No Crawl4AI runtime dependency.
- No scheduled auto publish in V1.7.2.
- No public user crawler entry.
