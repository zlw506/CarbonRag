# Policy Live Crawler Admin Interaction Hotfix

## Summary

Fix the admin live policy crawler surface so it is an actually testable Scrapy workflow instead of a passive status panel. The admin page must show the official allowlist sources, expose a manual crawl button for each source, surface Scrapy availability and runtime errors, and refresh runs/candidates after actions.

## Scope

- M3 Frontend Admin UI
- M5 Knowledge / File / RAG policy crawler boundary

## Key Decisions

- Official allowlist is limited to `gov.cn`, `ndrc.gov.cn`, `mee.gov.cn`, `miit.gov.cn`, `fgw.beijing.gov.cn`, and `beijing.gov.cn`.
- Live crawling remains admin-triggered and review-first.
- Scheduled public crawling remains disabled by default.
- Crawl candidates must stay outside `/ask` and public retrieval until admin publication.
- Scrapy should be available in the normal backend development install, while still failing with explicit diagnostics if the runtime environment uses a Python interpreter without Scrapy.
- The production crawler uses a shared Scrapy spider module for both local execution and optional Scrapyd deployment; Scrapy/Scrapyd remain external dependencies, not vendored source copies.
- Crawled binary policy attachments are staged as bytes from base64 payloads so PDF/OFD candidates are not corrupted before parser processing.

## Risks

- Real official sites can fail due to network, robots, TLS, or rate limits.
- Admin UI touches a wide page, so frontend typecheck/build is required.
- Scrapy dependency increases backend install size, but it is the chosen production crawler layer for this feature.
