# CarbonRag V1.4.4 上游数据源决策

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

V1.4.4 seed 数据采用生态环境部、国家统计局发布的 2023 年全国电力平均二氧化碳排放因子：

```text
0.5306 kgCO2/kWh
```

## 绿电与 market-based

Market-based 口径只预留字段。没有绿电合同、绿证或交易凭证时，不得把绿电直接算零。即使用户传入 `certified_green_kwh`，V1.4.4 仍使用 location-based 计算并返回 warning。

## 燃料因子

`natural_gas / diesel / gasoline / LPG / coal` 当前 seed 因子全部标记为 `source_type=demo`。在正式人工整理国家温室气体排放因子数据库或官方指南前，不得伪装为官方因子。
