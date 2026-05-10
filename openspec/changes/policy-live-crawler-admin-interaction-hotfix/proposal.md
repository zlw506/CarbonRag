# Policy Live Crawler Admin Interaction Hotfix

## Summary

Fix the admin live policy crawler surface so it is an actually testable Scrapy workflow instead of a passive status panel. The admin page must show the official allowlist sources, expose a manual crawl button for each source, surface Scrapy availability and runtime errors, and refresh runs/candidates after actions.

## Scope

- M3 Frontend Admin UI
- M5 Knowledge / File / RAG policy crawler boundary

## Key Decisions

- Official allowlist is limited to `gov.cn`, `ndrc.gov.cn`, `mee.gov.cn`, `miit.gov.cn`, `fgw.beijing.gov.cn`, and `beijing.gov.cn`.
- Live crawling supports manual admin trigger and default scheduled automatic refresh.
- Scheduled public crawling is enabled by default with strict official allowlist, robots, throttling, depth/page limits, and topic filtering.
- Crawled documents that match double-carbon policy or technical-standard topics are auto-published to `public_policy_web`, queued through `crawl_ingest`, and indexed immediately; candidate rows remain as audit records.
- Scrapy should be available in the normal backend development install, while still failing with explicit diagnostics if the runtime environment uses a Python interpreter without Scrapy.
- The production crawler uses a shared Scrapy spider module for both local execution and optional Scrapyd deployment; Scrapy/Scrapyd remain external dependencies, not vendored source copies.
- Crawled binary policy attachments are staged as bytes from base64 payloads so PDF/OFD candidates are not corrupted before parser processing.
- The six default sources are official search/listing entrypoints under `gov.cn`, `ndrc.gov.cn`, `mee.gov.cn`, `miit.gov.cn`, `fgw.beijing.gov.cn`, and `beijing.gov.cn`, not one fixed detail page.

## Risks

- Real official sites can fail due to network, robots, TLS, or rate limits.
- Admin UI touches a wide page, so frontend typecheck/build is required.
- Scrapy dependency increases backend install size, but it is the chosen production crawler layer for this feature.
