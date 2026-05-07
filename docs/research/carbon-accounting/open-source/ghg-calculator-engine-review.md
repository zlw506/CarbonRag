# ghg-calculator 计算引擎参考审查

本地参考路径：`3rdparty/ghg-calculator-main/ghg-calculator-main`

## 许可证判断

- 本地 README 标称 MIT。
- 本地下载目录未发现 `LICENSE` 文件。
- `gh repo view starrybodies/ghg-calculator --json licenseInfo` 返回 `licenseInfo=null`。
- V1.4.4 只做结构参考，不复制源码、不复制因子数据。

## 最值得借的结构

- `ActivityRecord`：统一活动数据入口，避免继续扩展三字段请求。
- `GHGCalculator`：总调度器按 scope/category 路由。
- `FactorRegistry`：因子加载、筛选、搜索、版本管理。
- `UnitConverter`：单位归一与业务单位定义。
- Scope calculators：Scope 1 stationary/mobile、Scope 2 electricity 分层实现。
- Result model：分项结果、总量、报告输出分离。

## CarbonRag V1.4.4 映射

- `ActivityRecord` -> `CarbonActivityItem`
- `GHGCalculator` -> `CarbonCalculationEngine`
- `FactorRegistry` -> `backend/app/carbon/factors/registry.py`
- `UnitConverter` -> `backend/app/carbon/units.py`
- Scope calculators -> `scope1.py` / `scope2.py`
- Result model -> `factor_snapshot / unit_conversion_trace / formula_trace`

## 本轮不借

- 不借国外因子数据库。
- 不借完整 Scope 3。
- 不借 MCP server、Claude Code skill、完整 CLI。
- 不借 HTML report 生成。
