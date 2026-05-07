## Context

Current calc-carbon is a useful first chain, but it is too rigid for enterprise carbon accounting. The useful reference from `ghg-calculator` is the engine shape: universal activity record, factor registry, unit conversion, scope calculator routing, and result objects. The useful reference from EPFL co2-calculator is model discipline around factor/data-entry/result binding. EPFL is GPL-3.0, so CarbonRag must not copy code.

## Decisions

### Decision 1: Add V2 without breaking legacy payloads

The public endpoint remains `POST /api/v1/calc-carbon`. Legacy three-field payloads are internally converted into `activity_items[]`.

### Decision 2: Factor selection is explicit and snapshot-based

Each calculated line stores the full factor snapshot used at calculation time. Reports and audits must not depend only on a mutable `factor_id`.

### Decision 3: Official and demo factors are separated

Official Scope 2 electricity uses MEE/NBS source metadata. Fuel combustion seed factors remain `source_type=demo` until manually curated from official factor database sources.

### Decision 4: Market-based electricity is not silently zeroed

Green electricity and market-based Scope 2 are reserved in this baseline. Even if certified green kWh is provided, V1.4.4 uses location-based calculation and emits a warning.

### Decision 5: Scope 3 is a reserved boundary

Scope 3 input structures may be introduced later, but V1.4.4 does not calculate Scope 3.

## Risks

- Factor source confusion: mitigated by explicit `source_type` and warning fields.
- Backward compatibility risk: mitigated by preserving old payload fields and response top-level fields.
- Report regression: mitigated by keeping carbon result trace IDs, breakdown, citations, and session binding.
