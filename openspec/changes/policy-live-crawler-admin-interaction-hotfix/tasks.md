## 1. Spec And Coordination

- [x] 1.1 Record this hotfix change and validate OpenSpec.
- [x] 1.2 Post Mattermost PLAN before editing.

## 2. Backend Crawler Usability

- [x] 2.1 Tighten official allowlist to the six approved domains.
- [x] 2.2 Ensure seeded source allowed domains use the approved parent domains.
- [x] 2.3 Make Scrapy part of the normal backend dependency set for real local testing.
- [x] 2.4 Add tests for the approved allowlist and real Scrapy availability metadata.

## 3. Admin UI Interaction

- [x] 3.1 Show official allowlist source cards even if the API source list is empty.
- [x] 3.2 Add per-source manual crawl controls with clear loading, disabled, failed, unavailable, and success states.
- [x] 3.3 Refresh status, runs, and candidates after manual crawl/publish/reject.
- [x] 3.4 Surface backend error details and Scrapy install/runtime hints.

## 4. Verification

- [x] 4.1 Run targeted backend policy crawler/admin tests.
- [x] 4.2 Run a real Scrapy smoke against an official allowlist source from the local backend environment.
- [x] 4.3 Run frontend typecheck and build.
- [x] 4.4 Run `openspec validate policy-live-crawler-admin-interaction-hotfix --strict` and `openspec validate --all`.
- [x] 4.5 Run GitNexus detect changes.

## 5. Production Crawler Hardening On Latest Main

- [x] 5.1 Rebase the hotfix work onto #1 latest `upstream/main`.
- [x] 5.2 Promote the Scrapy spider into a reusable module shared by local Scrapy and Scrapyd deployment.
- [x] 5.3 Add a `scrapy.cfg` and Scrapy settings module so the same spider can be deployed to Scrapyd.
- [x] 5.4 Preserve official allowlist, robots, depth/page, delay, concurrency, timeout, and review gate for both backends.
- [x] 5.5 Support binary crawled payloads such as PDF/OFD by staging base64 payloads as bytes.
- [x] 5.6 Ensure `scripts/dev-local.ps1` exposes `.venv` site-packages to Uvicorn reload children on Windows.
- [x] 5.7 Re-run targeted tests, real official-site Scrapy smoke, frontend checks, OpenSpec, and GitNexus detect changes.

## 6. Review Feedback Closure

- [x] 6.1 Change the six official sources to domain/listing entrypoints instead of a single fixed policy detail page.
- [x] 6.2 Capture only likely policy/document candidates from listing crawls and prioritize policy-looking links.
- [x] 6.3 Store candidate summary, content length, crawl depth, seed URL, and response URL in review metadata.
- [x] 6.4 Process `crawl_ingest` immediately after publish and write indexing success/failure into candidate review notes.
- [x] 6.5 Show candidate policy details in Admin pending-review list before publish/reject decisions.
