## Why

V1.4.4 已把 `calc-carbon` 从三字段计算器升级为 factor-driven baseline，但仍然主要依赖兼容表和 JSON 快照。企业基础碳核算要继续往报告、复算、纠错、审计和因子库导入走，必须保存原始活动数据、证据字段、因子快照、计算行和 scope summary。

本轮 V1.4.5 目标是把“能算”升级成“可回放、可审计、可解释、能接官方因子”。

## What Changes

- 新增 `carbon_inventories`、`carbon_activity_items`、`carbon_calculation_lines`、`carbon_factor_snapshots`、`carbon_evidence_references`、`carbon_inventory_summaries`。
- `carbon_calculations` 保持兼容，并补充 `inventory_id`、原始 activity JSON、scope summary 和 factor count。
- 旧三字段兼容只转换非零 activity，避免只填电力时生成天然气/柴油 warning。
- `activity_items[]` 新增 `province`、`data_quality`、`evidence_reference`、`source_document_id`、`entry_method`、`requested_factor_id`。
- 拆分并加载多文件因子源：官方 2023 中国电力因子、燃料 guidance seed、旧 V2 seed。
- `FactorRegistry` 增加官方/地区/年份/上级地区/guidance/demo 的优先级与 fallback warning。
- 响应新增 `inventory_id`、`total_kgco2e`、`scope_summary`、`activity_count`、`official_factor_count`、`fallback_factor_count`。

## Capabilities

### Modified Capabilities

- `carbon-report-feedback`: calc-carbon 结果从演示快照升级为可信 inventory 事实链。

## Impact

- Affected module: M6 Carbon / Report / Feedback.
- Affected backend areas: `backend/app/carbon/**`, `backend/app/runtime_db/schema.py`, carbon tests.
- Affected data: `data/factors/electricity_cn_2023_official.json`, `data/factors/fuel_combustion_cn_guidance_seed.json`.
- No frontend UI change in V1.4.5.
- No RAG / LightRAG implementation change; V1.3.x remains owned by #2.
