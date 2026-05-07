# factors 目录说明

本目录用于存放排放因子样例、核算模板和辅助说明文件。

## 当前 v0.1.9A 基线
- 当前主文件：`carbon_factors_v0_1_9a.json`
- 当前只支持 3 类活动数据：
  - `electricity`
  - `natural_gas`
  - `diesel`
- 当前因子仅用于本地 demo 和链路验证，不代表正式审计或正式盘查口径

## 当前 V1.4.4 因子驱动基线
- 新主文件：`carbon_v2_seed.json`
- 新结构使用 `factor_records[]`，支持按 `scope / activity_category / activity_name / region / year / source_type` 选择因子。
- Scope 2 外购电力当前优先使用生态环境部、国家统计局发布的 2023 年电力二氧化碳排放因子公告。
- `natural_gas / diesel / gasoline / LPG / coal` 当前仍为 demo 因子，必须保留 `source_type=demo` 和“不用于正式盘查或审计”的说明。
- CEADs 仅作为宏观清单方法论参考，不作为企业直接计算因子源。

## 因子文件字段要求
每条因子至少包含：
- `factor_id`
- `name`
- `unit`
- `value`
- `source`
- `source_url`
- `note`
- `version`

## 允许内容
- 排放因子示例表
- 核算模板
- 说明性元数据

## 禁止内容
- 运行输出文件
- 临时调试文件
- 无法确认来源的核算系数
- 真实企业私有数据
