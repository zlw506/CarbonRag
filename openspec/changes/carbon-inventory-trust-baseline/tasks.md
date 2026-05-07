# Tasks

## Data

- [x] Add `electricity_cn_2023_official.json` with national, residual, fossil, grid-region, and province factors.
- [x] Add `fuel_combustion_cn_guidance_seed.json` with `guidance_default` fuel factors.
- [x] Keep `carbon_v2_seed.json` as compatibility seed and load multiple factor files.

## Backend

- [x] Extend `CarbonActivityItem` evidence fields.
- [x] Filter zero legacy fields during conversion.
- [x] Extend `FactorRecord` and `FactorRegistry` priority/fallback metadata.
- [x] Add inventory response fields and scope summary.
- [x] Add SQLite/PostgreSQL tables for inventories, activities, lines, factor snapshots, evidence, and summaries.
- [x] Persist V2 request, raw activity payload, calculation lines, factor snapshots, and evidence references.
- [x] Preserve `carbon_calculations` compatibility.

## Verification

- [x] Add zero-filter test.
- [x] Add official electricity factor selection test.
- [x] Add fuel guidance seed warning test.
- [x] Add factor priority test.
- [x] Add inventory persistence and evidence field tests.
- [x] Add inventory summary test.
- [x] Run `openspec validate carbon-inventory-trust-baseline --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend pytest.

## Archive

- [ ] Archive after V1.4.5 is validated and accepted.
