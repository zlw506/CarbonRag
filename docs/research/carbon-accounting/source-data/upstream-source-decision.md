# CarbonRag V1.4.5 上游数据源决策

## 结论

CarbonRag 第一阶段碳核算不再以开源项目内置因子作为正式来源。因子来源优先级固定为：

1. 生态环境部 / 国家统计局电力二氧化碳排放因子：Scope 2 外购电力第一优先源。
2. 国家温室气体排放因子数据库：第一阶段因子库核心方向。
3. 中国标准、行业指南、报告规范：用于校准口径和报告说明。
4. CEADs：宏观清单和方法论参考，不作为企业直接计算因子源。
5. 开源项目因子：只做结构测试或 demo，不作为中国企业正式因子。

## CEADs 定位

CEADs 的价值在于宏观清单组织方式：生产端、领土端、部门、能源品种、能源平衡表、投入产出表和过程排放。它适合指导 CarbonRag 理解上游核算体系，不适合直接作为企业填报几度电、几立方米天然气后的因子源。

## Scope 2 外购电力

企业外购电力第一阶段使用公式：

```text
location_based_emission_kgco2 = purchased_electricity_kwh × grid_average_factor_kgco2_per_kwh
```

V1.4.5 将生态环境部、国家统计局发布的 2023 年电力二氧化碳排放因子拆成独立 seed 文件：

```text
data/factors/electricity_cn_2023_official.json
```

当前录入范围包括：

- 全国平均：0.5306 kgCO2/kWh
- 全国剩余组合：0.6096 kgCO2/kWh
- 全国化石能源电力：0.8273 kgCO2/kWh
- 七大区域平均因子
- 31 个省级平均因子

## 绿电与 market-based

Market-based 口径仍只作为受控预留。没有绿电合同、绿证或交易凭证时，不得把绿电直接算零。即使用户传入 `certified_green_kwh`，V1.4.5 也必须通过 warning 说明 market-based / green power 口径尚未完整启用。

## 燃料因子

V1.4.5 将燃料因子从 `demo` 升级为单独的 guidance seed：

```text
data/factors/fuel_combustion_cn_guidance_seed.json
```

其中 `natural_gas / diesel / gasoline / LPG / coal / fuel_oil / kerosene` 等均标记为 `source_type=guidance_default`，并强制返回 warning：

```text
该因子来源于公共机构核算指南缺省值，仅用于基础演示和缺少更权威因子时参考；企业正式核算应优先使用国家温室气体排放因子数据库或适用行业指南。
```

不得把 guidance seed 伪装为企业正式官方因子。国家温室气体排放因子数据库仍是后续人工导入正式燃料因子的核心来源。

## 可信链路要求

从 V1.4.5 起，每次计算必须至少保留：

- 原始请求 payload
- 原始 `activity_items[]`
- `organization_id / facility_id / period_start / period_end / inventory_standard`
- 活动数据证据字段：`data_quality / evidence_reference / source_document_id / entry_method`
- 因子快照：计算时实际使用的因子完整值和来源信息
- 单位换算 trace
- 公式 trace
- scope summary 与 fallback warning
