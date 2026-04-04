# Claw-Code To CarbonRag Mapping

版本：v0.1.4

| claw-code 模块/概念 | 它解决的问题 | CarbonRag 对应位置 | 本轮是否落地 | 备注 |
| --- | --- | --- | --- | --- |
| `rust/crates/api` | 统一供应商访问与传输边界 | `backend/app/ai_runtime/providers/` | 是 | CarbonRag 保留 OpenAI-compatible chat / embedding provider |
| `rust/crates/runtime` | 统一会话、调度、权限和主执行链 | `backend/app/ai_runtime/runtime/` | 是 | 当前只冻结 orchestrator / context / guards / formatter |
| `rust/crates/tools` | 工具注册与调用约束 | `backend/app/ai_runtime/tools/` | 是 | 当前只保留 5 个双碳业务 stub |
| `rust/crates/commands` | 将不同交互意图映射为运行模式 | `backend/app/ai_runtime/modes/` | 是 | 不照搬 slash command，只转译为 ask / carbon / report mode |
| `src/services` | 将运行时与业务服务拆层 | `backend/app/services/` + `ai_runtime` 分界 | 否 | 位置保留，暂不扩展服务层 |
| `src/state` / `src/memdir` | 给 session / memory 预留稳定位置 | `context_builder` 的 `session_state` 与 `memory_slot` | 是 | 当前只保留结构占位，不做真实 memory |
| `src/skills` | 为能力组合与调用治理留边界 | 未来 skills 能力位，当前未落目录 | 否 | 本轮只在文档中冻结边界，不实现 registry |
| `src/hooks` / `src/plugins` | 运行时扩展与治理入口 | 文档边界，不进代码实现 | 否 | 当前明确不做 plugin / hook runtime |
| `claw-cli` | 产品入口与交互表面 | CarbonRag Web 前后端，不对等映射 | 否 | CarbonRag 不采用 coding-agent CLI 作为产品壳 |

## 本轮结论

本轮真正落地的不是 claw-code 的“功能数量”，而是它的分层方式。CarbonRag 只把能稳定服务自身产品形态的部分吸收为后端骨架，其余能力继续留在文档边界中。
