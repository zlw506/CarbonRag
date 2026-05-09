## Overview

V1.4.8 builds a CarbonRag runtime carbon factor database that uses CarbonStop CCDB public page/gateway data as the first public benchmark source. The implementation separates five concerns:

1. Factor catalog storage and versioned source metadata.
2. User-facing search/detail APIs.
3. Admin import/maintenance workflow.
4. Carbon calculation factor resolution.
5. CarbonStop CCDB public-data adapter with source attribution.

CarbonStop CCDB exposes public category, factor and source fields through the page runtime. CarbonRag V1.4.8 imports the public fields that are visible to normal visitors, preserves CarbonStop CCDB attribution plus the original institution/source fields, and keeps the raw row snapshot in metadata. The adapter must not access login-only, paid, private or non-public data.

## Data Model

Runtime database tables:

- `carbon_factor_sources`
  - `source_id`
  - `title`
  - `publisher`
  - `source_url`
  - `license`
  - `published_year`
  - `source_type = official | public_dataset | internal_curated | demo | authorized_partner`
  - `created_at`, `updated_at`
- `carbon_factor_records`
  - `factor_id`
  - `source_id`
  - `name`
  - `category`
  - `industry`
  - `scope`
  - `region`
  - `year`
  - `gas`
  - `factor_value`
  - `factor_unit`
  - `activity_unit`
  - `co2e_unit`
  - `quality = official | curated | imported | demo | deprecated`
  - `is_enabled`
  - `version`
  - `metadata_json`
  - `created_at`, `updated_at`
- `carbon_factor_aliases`
  - `alias_id`
  - `factor_id`
  - `alias`
  - `locale`
- `carbon_factor_import_jobs`
  - `job_id`
  - `owner_user_id`
  - `source_kind = carbonstop_public | json | csv | seed | authorized_adapter`
  - `status = queued | running | succeeded | failed`
  - `summary_json`
  - `error_message`
  - `created_at`, `updated_at`

## API Shape

User APIs:

- `GET /api/v1/carbon-factors`
  - Filters: `q`, `category`, `industry`, `region`, `year`, `source_type`, `quality`, `unit`, `page`, `page_size`.
  - Returns factor summaries with source summary and citation fields.
- `GET /api/v1/carbon-factors/{factor_id}`
  - Returns full factor details, aliases, source metadata and calculation-ready unit fields.
- `GET /api/v1/carbon-factor-sources`
  - Returns source catalog for filters and source inspection.
- `GET /api/v1/carbon-factors/facets`
  - Returns categories, industries, regions, years and source types for page filters.

Admin APIs:

- `GET /api/v1/admin/carbon-factor-import-jobs`
- `POST /api/v1/admin/carbon-factor-import-jobs`
- `POST /api/v1/admin/carbon-factor-import-jobs/carbonstop-sync`
- `POST /api/v1/admin/carbon-factor-import-jobs/{job_id}/retry`
- `PATCH /api/v1/admin/carbon-factors/{factor_id}`

## CarbonStop CCDB Public Adapter

The adapter mirrors the public page behavior:

- Fetch `https://www.carbonstop.com/ccdb` to read the public industry/category dictionary and hot keywords.
- Call the same public gateway endpoint used by the page for each visible category pair:
  - `POST https://gateway.carbonstop.com/management/system/website/queryFactorListWebsite_classify`
  - signature: `MD5("website_ccdb" + classify + industry)`
  - response body field: `responseData`
  - public bundle decrypts `responseData` with AES-128-ECB and key `carbon@stp2060ja`.
- Normalize rows into `FactorRecord` while preserving raw row fields in `metadata_json`.
- Group source metadata by original `institution`, `source`, `documentType` and `year`.
- Attribute imported records to both:
  - `CarbonStop CCDB 中国碳数据库`
  - original row fields such as `institution`, `source`, `sourceLevel`, `documentType`.

The adapter is deterministic and idempotent: the same CCDB row id maps to the same `factor_id`.

## Factor Resolution

`FactorRegistry` resolves factors in this order:

1. Runtime DB enabled factor records matching explicit `factor_id`.
2. Runtime DB enabled factor records matching activity category, region, year, gas and unit.
3. CarbonStop CCDB public seed/imported records already in runtime DB.
4. Existing curated seed JSON registry.
5. Existing demo fallback with warnings, where supported.

Every calculation stores a factor snapshot, including `factor_id`, source metadata, unit fields, quality and version. Reports continue reading snapshots from stored calculations.

## Frontend

Add a `碳因子库` workbench page:

- Search-first layout with hot keywords.
- Category/industry filters.
- Factor cards showing name, value/unit, region/year, quality tag and source.
- Detail drawer showing source, aliases, unit semantics, applicable scope and citation.
- Admin-only import/maintenance entry is separate from normal user browsing.

Carbon calculation pages may link to factor details when showing factor citations. They do not need full manual factor picker in the first implementation unless the API and registry are ready.

## Data Governance

Allowed sources for V1.4.8:

- CarbonStop CCDB public page/gateway fields visible to normal visitors, with attribution and raw snapshots.
- Existing CarbonRag seed files as fallback.
- Public official guidance documents and datasets with clear citation.
- User/admin supplied JSON/CSV where the uploader is responsible for rights.
- Future authorized adapters explicitly marked `authorized_partner`.

Disallowed:

- Accessing CarbonStop login-only, paid, private, rate-limited or non-public data.
- Importing CarbonStop rows without preserving CarbonStop and original-source attribution.
- Importing factors without source, license/status and publisher metadata.
