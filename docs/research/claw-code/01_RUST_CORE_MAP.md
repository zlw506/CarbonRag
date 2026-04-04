# Rust Core Map

## Workspace 事实

主快照 `rust/Cargo.toml` 的 workspace 采用：

- `members = ["crates/*"]`
- `edition = "2021"`
- `resolver = "2"`
- `unsafe_code = "forbid"`

本地真实 crate 名包含：

- `api`
- `runtime`
- `tools`
- `commands`
- `plugins`
- `compat-harness`
- `claw-cli`
- `lsp`
- `server`

本轮核心研究聚焦前七项。README 中把 `api` 概念性描述为 `api-client`，但本地实际目录名是 `api`。

## 核心 crate 职责

| crate | 当前职责 | 对 CarbonRag 的启发 |
| --- | --- | --- |
| `api` | Provider 抽象、OAuth、SSE、OpenAI-compatible 与 Claw provider 客户端 | 模型供应商访问应独立于业务服务层 |
| `runtime` | session、prompt、permissions、MCP、conversation loop、config | runtime 应是独立层，不要直接塞进业务路由 |
| `tools` | 工具规格注册与执行框架 | 工具系统要有独立注册表，而不是散落在页面或接口层 |
| `commands` | slash command 注册表、skills 发现、config 报告 | 命令层与 runtime/tool 层应分离 |
| `plugins` | 插件模型、bundled hooks、扩展入口 | 插件要先是边界，再谈功能数量 |
| `compat-harness` | 上游兼容壳与编辑器对接表面 | 兼容层应晚于核心 runtime 稳定后再考虑 |
| `claw-cli` | CLI 主入口、渲染、输入、bootstrap/init | 产品入口不应反向污染 runtime 核心 |

## Rust 内核的主数据流

当前可抽象为：

1. `api` 负责供应商与传输协议
2. `runtime` 负责会话、提示词、权限、MCP 与主循环
3. `tools` 负责工具注册与执行
4. `commands` 负责交互命令表面
5. `plugins` 负责扩展装配点
6. `claw-cli` 负责终端入口与展示

这套拆分对 CarbonRag 的意义在于：

- `provider` 不应直接长进业务路由
- `runtime` 不应与前端页面耦合
- `tool` 不应只是后端 util 函数堆
- `plugin/hooks/skills` 应先建概念边界，再决定是否做

## 本轮重点观察点

目录级差异已暴露出三个主要热点：

- `fix_plugin_loading_parity_snapshot` 主要集中在 `rust/crates/commands`、`rust/crates/tools`、`rust/crates/plugins`
- `fix_skill_invoke_snapshot` 主要集中在 `rust/crates/commands`、`rust/crates/tools`、`rust/crates/claw-cli`
- `fix_ui_parity_snapshot` 额外引入了 `rust/crates/runtime/src/skills.rs` 与 `claw-cli/tests/prompt_json_transport.rs`

这说明对方仓库当前还在持续修补：

- plugin 装载路径
- skill 调用路径
- JSON/CLI 交互一致性

这些都属于“runtime 完整度”问题，而不是业务功能问题。
