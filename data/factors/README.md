# factors 目录说明

本目录用于存放排放因子样例、核算模板和辅助说明文件。

## 当前 v0.1.9A 基线
- 当前主文件：`carbon_factors_v0_1_9a.json`
- 当前只支持 3 类活动数据：
  - `electricity`
  - `natural_gas`
  - `diesel`
- 当前因子仅用于本地 demo 和链路验证，不代表正式审计或正式盘查口径

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
