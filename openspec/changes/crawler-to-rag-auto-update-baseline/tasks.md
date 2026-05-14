# Tasks: crawler-to-rag-auto-update-baseline

## 1. Governance and Defaults

- [x] Add V1.7.0 architecture, adoption notes, and plan documents.
- [x] Add OpenSpec delta for crawler-to-RAG publishing.
- [x] Disable scheduled crawler and auto publish by default.
- [x] Keep manual crawler trigger enabled.

## 2. Candidate Artifacts

- [x] Preserve raw candidate storage path.
- [x] Write cleaned text and markdown artifacts.
- [x] Record canonical URL, content hash, previous hash, change type, skip reason, backend, robots, duration, and error stage metadata.
- [x] Add dedupe metadata for unchanged content.

## 3. RAG Publish Bridge

- [x] Add `publish_crawled_candidate_to_rag_kb`.
- [x] Create or reuse the shared official policy RAG KB.
- [x] Create a `public_policy` RagDocument from candidate markdown/text.
- [x] Run quick pipeline and write RAG IDs/status back to candidate metadata.
- [x] Add admin `publish-to-rag` endpoint.

## 4. Admin UI and Scripts

- [x] Add Publish to RAG service call.
- [x] Show RAG KB/doc/index/smoke status in admin crawler candidates.
- [x] Keep legacy publish visible but secondary.
- [x] Add local Scrapy smoke script.
- [x] Add RAG publish smoke script.

## 5. Validation

- [ ] `openspec validate crawler-to-rag-auto-update-baseline --strict`
- [ ] `openspec validate --all`
- [ ] Targeted backend pytest.
- [ ] Frontend typecheck/build.
- [ ] `git diff --check`
- [ ] `gitnexus detect_changes`
