# Design

## Backend

- Keep `PolicyCrawlerScheduler` and `ScrapyCrawlerProvider` as the execution boundary.
- Tighten the official allowlist constants and seeded source `allowed_domain` values to the six approved domains.
- Add status metadata that helps Admin explain whether Scrapy is truly available in the current backend interpreter.
- Keep manual crawl behavior synchronous for the first usable version so the Admin button can immediately show a run record and candidate count.
- Promote `CarbonRagPolicySpider` to a reusable Scrapy spider module shared by local Scrapy subprocess runs and optional Scrapyd deployment.
- Add `backend/scrapy.cfg` and Scrapy settings so operators can deploy the same spider into Scrapyd without copying upstream source code into CarbonRag.
- Pass robots, depth/page, delay, concurrency, timeout, and user-agent constraints to Scrapyd `schedule.json` through Scrapy settings.
- Keep crawled binary policy attachments safe by carrying them as base64 during crawler transport and writing them back as bytes when staging candidates.

## Frontend

- Render the six official sources even when the backend returns an empty source list, using fallback display data that still calls backend source ids.
- Add a compact control surface per source:
  - source title, URL, allowlist domain
  - last status and last error
  - manual crawl button
  - focused run/candidate refresh behavior
- Add explicit empty, unavailable, and failed guidance:
  - unavailable means the backend Python environment lacks Scrapy or cannot import it
  - failed means the crawler ran but the target site/network failed
  - succeeded with zero candidates should still be visible

## Validation

- Backend targeted policy crawler/admin tests.
- Frontend typecheck/build.
- OpenSpec validation.
- GitNexus detect changes before commit/PR.
