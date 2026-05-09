## 1. Specification and Governance

- [x] Create OpenSpec proposal, design and deltas for V1.4.8.
- [x] Post #3 Mattermost PLAN and receive local go-ahead to implement.
- [x] Document CarbonStop CCDB public page/gateway as the primary public benchmark/source and forbid non-public/private data access.

## 2. Runtime Data Model

- [x] Add SQLite and PostgreSQL tables: `carbon_factor_sources`, `carbon_factor_records`, `carbon_factor_aliases`, `carbon_factor_import_jobs`.
- [x] Add bootstrap/migration tests for both runtime modes.
- [x] Add CarbonStop CCDB public adapter and importer as the primary public seed source.
- [x] Keep existing `data/factors/**` importer as fallback with source and quality metadata.

## 3. Backend API

- [x] Add user factor search, detail, source and facet routes.
- [x] Add admin import job and factor enable/disable routes.
- [x] Add admin CarbonStop public sync route.
- [x] Add pagination, filtering and normalized response schemas.
- [ ] Add route tests for search, filters, detail, admin import, invalid input and auth boundaries.

## 4. Carbon Engine Integration

- [x] Update `FactorRegistry` to resolve runtime DB factors before seed fallback.
- [ ] Preserve factor snapshots in calculation results.
- [x] Add tests proving runtime registry reads DB factors and falls back to seed when DB is unavailable.

## 5. Frontend

- [x] Add `碳因子库` navigation entry and route.
- [x] Build search-first factor database page with category filters, cards and detail drawer.
- [ ] Link carbon calculation factor citations to factor details where possible.
- [ ] Add admin-only import/maintenance affordance without exposing it to normal users.
- [x] Add frontend smoke coverage through typecheck/build and manual page checks.

## 6. Verification

- [x] `openspec validate carbon-factor-database-foundation --strict`
- [x] `openspec validate --all`
- [x] Backend tests for factor DB and calc integration.
- [x] `npm.cmd run typecheck`
- [x] `npm.cmd run build`
