# AI Runtime Tool Boundary

版本：v0.1.4

## 当前允许的工具面

v0.1.4 只允许双碳业务 stub 工具存在于 runtime：

- `policy_retrieve`
- `enterprise_retrieve`
- `carbon_factor_lookup`
- `carbon_calc`
- `report_draft`

这些工具当前只承担“结构占位”和“调度受控”的职责，不承担真实检索、真实计算或真实报告生成。

## 当前工具允许做什么

- 返回固定结构的 stub 结果
- 暴露统一工具名与工具输出格式
- 作为 ask / carbon / report mode 的白名单成员
- 为后续真实业务实现保留稳定注册位

## 当前工具明确不允许做什么

- 不允许 shell
- 不允许任意文件写
- 不允许任意网页抓取
- 不允许任意系统调用
- 不允许绕过 `ToolRegistry` 私自执行能力
- 不允许直接访问模型供应商 API

## 当前边界为什么要收紧

CarbonRag 当前是双碳垂直产品，不是通用 coding-agent。runtime 先要可控，之后才谈能力扩展。如果在 v0.1.4 就引入通用执行面，只会把未来 ask / calc / report 的业务边界打穿。

## 后续扩展原则

- 新工具必须先定义业务归属和输出 schema
- 新工具必须先进入 registry 和 mode 白名单，再考虑真实实现
- 真实工具落地前，要先明确数据边界、审计点和失败回退方式
