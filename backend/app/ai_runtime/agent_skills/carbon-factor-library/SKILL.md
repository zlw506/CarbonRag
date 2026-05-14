---
name: carbon-factor-library
description: Use when CarbonRag needs carbon factors or emission factors for carbon accounting, report analysis, activity data calculation, or questions mentioning 碳因子, 排放因子, 碳核算, 排放量, 外购电力, 天然气, 柴油, 汽油, 蒸汽, LPG, 煤, 水, 制冷剂, R410A, R134a. First identify needed activity names from the compact factor index, then call carbon_factor_lookup for detailed records instead of loading every factor.
---

# Carbon Factor Library

Use this skill to keep carbon-factor reasoning selective and auditable. It is a progressive-disclosure index for CarbonRag's local carbon factor library.

## Workflow

1. Read `references/carbon-factor-index.md` when the user asks for carbon factors, emission factors, carbon accounting, activity amounts, report emissions, or factor availability.
2. Identify the likely activity keys and aliases before requesting details.
3. Call `carbon_factor_lookup` with a query that includes the exact activity names and `top_k` high enough for the requested categories.
4. Use only returned factor records for calculation-ready values.
5. If the index or lookup has no matching record, say the factor is not currently available and do not invent a value.

## Rules

- Do not load or summarize every factor record into the model context.
- Treat `carbon-factor-index.md` as the directory of names and aliases, not as the source of numeric factor truth.
- Treat `carbon_factor_lookup` results as the calculation source for factor value, unit, region, year, and source.
- When the user asks "how many factors are visible", distinguish total registry records from the current turn's selected hits.
- For report calculations, map extracted activity amounts to factors first, then calculate `activity amount * factor`, with unit assumptions stated.

## References

- `references/carbon-factor-index.md`: compact activity and factor-name index generated from the local registry.
