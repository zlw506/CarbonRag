## Context

V1.4.4 的 factor-driven engine 已有 ActivityItem、FactorRegistry、UnitConverter、Scope calculator 和 ResultSnapshot。V1.4.5 不重做 UI，也不扩行业公式，而是补企业核算可信链路：活动数据原文、证据字段、因子快照、计算行、scope summary 和 fallback 说明。

## Decisions

### Decision 1: Use detailed inventory tables as source of truth

`carbon_calculations` 继续服务旧 report/session 查询，但 V1.4.5 的新事实源是 `carbon_inventories` 与子表。这样可以回放原始请求、逐条检查 activity、追溯因子和证据。

### Decision 2: Legacy fields generate only non-zero activity items

旧三字段兼容层只把 `> 0` 的字段转成 activity item。否则只填外购电力也会出现燃料 warnings，误导用户以为系统使用了燃料数据。

### Decision 3: Official electricity factors are separated from guidance/demo fuels

2023 中国电力因子进入独立 official seed。燃料缺省值进入 `guidance_default` seed，并强制 warning。旧 `demo` 因子仍保留为最低优先级 fallback。

### Decision 4: Factor fallback must be visible

优先级固定为：用户指定因子 > 同地区同年份官方 > 同地区最近年份官方 > 上级地区官方 > guidance_default > demo。只要不是精确官方命中，就通过 `warnings[]` 说明。

### Decision 5: Market-based Scope 2 remains reserved

V1.4.5 仅保留 market-based/residual/fossil factor structures 和 `scope2_market_kgco2e=null`，不把绿电任意算零。后续需要凭证质量规则再启用 market-based。

## Data Sources

- MEE/NBS 2023 electricity CO2 factors: first priority for Scope 2 location-based and residual/fossil structures.
- JS/T 303-2026 public institution guidance defaults: seed reference only, marked `guidance_default`.
- National GHG emission factor database: target source for future manual official import, no automated sync in this change.
- CEADs: macro inventory methodology reference only, not enterprise direct factor source.

## Risks

- Province factor transcription risk: mitigated by locking key national/grid/province values in tests and keeping official source metadata.
- Backward compatibility risk: mitigated by preserving old endpoint and top-level response fields.
- Report regression risk: mitigated by keeping trace id, breakdown, citations, factor snapshot, and session binding.
