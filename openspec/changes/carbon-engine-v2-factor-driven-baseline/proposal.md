## Why

CarbonRag 的 `calc-carbon` 已经能完成最小三字段核算，但它仍把活动数据、因子选择、单位换算和结果快照绑在一起，难以扩展到企业级 Scope 1 / Scope 2 填报。

V1.4.4 需要建立 factor-driven carbon engine：用统一活动数据、因子注册表、单位归一、公式 trace 和 factor snapshot 支撑后续企业试用级碳核算。

## What Changes

- 保留旧 `electricity_kwh / natural_gas_m3 / diesel_l` 请求兼容。
- 新增 `activity_items[]` 输入模型。
- 新增因子驱动计算路径：ActivityItem -> FactorRegistry -> UnitConverter -> Scope calculator -> ResultSnapshot。
- Scope 1 先支持 stationary/mobile combustion 最小版。
- Scope 2 先支持 purchased electricity location-based。
- market-based green power、purchased heat、Scope 3 只预留，不完整实现。
- 新增 `data/factors/carbon_v2_seed.json`，官方电力因子与 demo 燃料因子明确区分。

## Capabilities

### Modified Capabilities

- `carbon-report-feedback`: calc-carbon 从三字段最小计算器升级为 factor-driven carbon engine baseline。

## Impact

- Affected module: M6 Carbon / Report / Feedback.
- Affected backend areas: `backend/app/carbon/**`, runtime DB bootstrap, calc tests.
- Affected data: `data/factors/carbon_v2_seed.json`.
- No frontend UI change in V1.4.4.
- No RAG / LightRAG implementation change; V1.3.x remains owned by #2.
