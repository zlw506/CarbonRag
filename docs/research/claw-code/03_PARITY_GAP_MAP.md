# Parity Gap Map

## 研究口径

本文件基于主快照 `PARITY.md`，把对方仓库列出的 gap 改写成 CarbonRag 可直接复用的话语。重点不是判断对方“好不好”，而是识别一个成熟 AI runtime 需要哪些长期层。

## 核心差距重述

### plugins

对方结论：

- Rust 侧对 plugin 的 loader、install/update、enable/disable、命令表面都不完整

对 CarbonRag 的含义：

- plugin 不是“以后再说的装饰层”
- 如果未来要支持外部扩展，必须先定义插件边界、生命周期和治理点
- 当前轮次不实现 plugin，但要避免把扩展点写死

### hooks

对方结论：

- Rust 侧已能解析 hook config，但运行时执行链不完整

对 CarbonRag 的含义：

- hook 是运行时策略层，不是脚本附件
- 未来的审计、前置校验、后置记录，不应硬编码进单一路由

### skills

对方结论：

- Rust 侧只有本地 `SKILL.md` 级别能力，没有完整 registry / bundled / reload 体系

对 CarbonRag 的含义：

- “技能”不是几个 prompt 文本片段
- 若未来做行业流程技能，需要考虑注册、发现、版本和调用约束

### cli

对方结论：

- Rust CLI 仅具备本地核心能力，命令面远窄于更宽的 TS/Python 表面

对 CarbonRag 的含义：

- 产品入口层经常是最晚补齐、最容易欠债的一层
- CarbonRag 如果未来有 Admin、任务流、审查流，不要假设后端接口一写就等于入口完成

### assistant orchestration

对方结论：

- Rust 有核心 loop，但缺 hook-aware orchestration、remote/structured transport 等层

对 CarbonRag 的含义：

- “能调用模型”不等于“有 runtime”
- runtime 的完整性至少包括：会话、权限、工具调度、提示词构造、结构化输出、失败恢复

### services

对方结论：

- 核心 API / OAuth / MCP 有基础，但更宽服务生态缺失

对 CarbonRag 的含义：

- provider 只是服务层的一部分
- 后续若做知识拉取、报告生成、作业编排、审计记录，需要单独服务层而不是全部塞进 runtime

### memory / session integration

对方结论：

- Rust 侧在 session-memory、team-memory 这类围绕 skills 的整合上仍弱

对 CarbonRag 的含义：

- CarbonRag 后续若做记忆，必须区分：
  - 会话历史
  - 运行时工作记忆
  - 领域知识库
  - 企业侧私有上下文

## 对 CarbonRag 最重要的结论

`PARITY.md` 最有价值的不是“谁缺了哪些功能”，而是它把 runtime 需要长期经营的层次列得很清楚。对 CarbonRag 来说，本轮真正要吸收的是：

- 分层意识
- 边界意识
- 不把单次业务需求误当成 runtime 设计
