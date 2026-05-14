# Change: crawler-to-rag-auto-update-baseline

## Why

CarbonRag already has a policy crawler and a RAG-Pro knowledge base spine, but crawled policy candidates still primarily flow through the legacy knowledge publish path. V1.7.0 connects the existing official policy crawler to the RAG-Pro quick pipeline so official web updates can become searchable RAG documents after admin review.

## What Changes

- Keep Scrapy/Scrapyd as the current crawler executor.
- Study Crawl4AI for LLM-ready markdown extraction and Crawlab for source/run/task/log/result governance, without importing their full runtime.
- Change crawler defaults to manual trigger and reviewed publish.
- Record raw, cleaned text, markdown, dedupe, and failure metadata for candidates.
- Add an admin `publish-to-rag` action that creates a shared official-policy KB document and runs the quick RAG pipeline.
- Add crawler smoke scripts and admin UI status for RAG KB publish and index status.

## Out Of Scope

- No Firecrawl download or adoption.
- No Crawlab master/worker/MongoDB/SeaweedFS runtime.
- No scheduled auto publish in V1.7.0.
- No replacement of Scrapy/Scrapyd.
