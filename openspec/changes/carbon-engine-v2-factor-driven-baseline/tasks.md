# Tasks

## Research

- [x] Review local `ghg-calculator` structure as engine reference.
- [x] Review local EPFL `co2-calculator` structure as model/UX reference.
- [x] Write upstream source decision for CEADs, MEE/NBS electricity factors, national factor database, and open-source demo factors.

## Implementation

- [x] Add `ActivityItem / ActivityBatch` request model.
- [x] Add `FactorRegistry` and factor record schema.
- [x] Add minimal `UnitConverter`.
- [x] Add `CarbonCalculationEngine` and Scope 1 / Scope 2 routing.
- [x] Add result snapshot fields to API response and persistence.
- [x] Add `carbon_v2_seed.json` with official electricity and demo combustion factors.
- [x] Keep legacy three-field payload compatibility.

## Verification

- [x] Add V2 carbon tests for schema, registry, conversion, Scope 1, Scope 2, snapshots, and legacy compatibility.
- [x] Run targeted backend carbon/report/postgres tests.
- [x] Run full backend test suite.
- [x] Run `openspec validate carbon-engine-v2-factor-driven-baseline --strict`.
- [x] Run `openspec validate --all`.
- [x] Run frontend typecheck/build after API type updates.

## Archive

- [ ] Archive after V1.4.4 implementation PR is accepted and validated.
