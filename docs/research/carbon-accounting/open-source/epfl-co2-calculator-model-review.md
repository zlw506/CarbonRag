# EPFL co2-calculator 模型参考审查

本地参考路径：`3rdparty/co2-calculator-dev/co2-calculator-dev`

## 许可证判断

- 本地 `LICENSE` 为 GPL-3.0。
- CarbonRag 不复制 EPFL 源码、不迁移其前端结构、不复刻其数据库实现。
- 本轮只学习模型边界和模块化填报组织方式。

## 最值得借的结构

- `models/factor.py`：通用因子模型，classification / values / year 不是简单 key-value。
- `models/data_entry.py`：活动数据与填报入口分离。
- `models/data_entry_emission.py`：活动输入和排放结果绑定。
- `models/audit.py`：审计记录思想。
- `models/carbon_report.py`：报告模型和核算结果衔接。
- `year_configuration.py`：年份配置和因子适用期。

## CarbonRag V1.4.4 映射

- Factor 通用表 -> `FactorRecord`
- DataEntry -> `CarbonActivityItem`
- DataEntryEmission -> `CarbonBreakdownItem` + result snapshot
- Audit -> `formula_trace` + `factor_snapshot`
- CarbonReport -> 现有 report 的 `carbon_summary`
- YearConfiguration -> `year / valid_from / valid_to`

## 本轮不借

- 不借 GPL 代码。
- 不借 EPFL 专属业务模块。
- 不借 Quasar 前端。
- 不借完整 PostgreSQL/Alembic 架构。
- 不借实验室专属分类。
