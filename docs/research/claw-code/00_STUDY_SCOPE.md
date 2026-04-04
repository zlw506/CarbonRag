# claw-code 静态快照研究范围

## 研究目的

本轮研究 `claw-code` 的目标，不是把它接入 CarbonRag，也不是替换当前前后端，而是学习其 AI runtime 的分层方式，为 CarbonRag 后续的 runtime 设计提供一份可追踪的架构参照。

当前最有价值的不是某个单点功能，而是这些边界如何被拆开：

- provider / API
- runtime / session / prompt / permissions
- tools
- commands
- plugins / hooks / skills
- CLI / compat surface

## 当前样本边界

本轮只研究本地静态快照：

- `3rdparty/claw-code-study/main_snapshot/`
- `3rdparty/claw-code-study/fix_plugin_loading_parity_snapshot/`
- `3rdparty/claw-code-study/fix_skill_invoke_snapshot/`
- `3rdparty/claw-code-study/fix_ui_parity_snapshot/`

这些样本均用于：

- 目录树对照
- 关键文件对照
- 同路径文件 diff
- 文档与实现表面对照

这些样本不用于：

- git branch history 研究
- commit 演化分析
- merge-base 分析
- 任何形式的代码复制接入

## 固定阅读顺序

### 第 1 组：仓库自我定义

按以下顺序阅读主快照：

1. `README.md`
2. `CLAW.md`
3. `PARITY.md`

目的：

- 先确认仓库自述中的主实现表面
- 再确认当前 Rust 与更宽产品表面的差距
- 最后再进入代码层阅读

### 第 2 组：Rust 内核

按以下顺序阅读：

1. `rust/Cargo.toml`
2. `rust/crates/api`
3. `rust/crates/runtime`
4. `rust/crates/tools`
5. `rust/crates/commands`
6. `rust/crates/plugins`
7. `rust/crates/compat-harness`
8. `rust/crates/claw-cli`

说明：

- README 里把 `api` 概念性描述为 `api-client`
- 本地真实 crate 名是 `api`，文档一律按真实目录命名

### 第 3 组：src 成熟表面

优先研究这些目录：

1. `src/assistant`
2. `src/services`
3. `src/skills`
4. `src/hooks`
5. `src/plugins`
6. `src/state`
7. `src/memdir`
8. `src/cli`

### 第 4 组：静态快照差异

对照顺序固定：

1. `main_snapshot -> fix_plugin_loading_parity_snapshot`
2. `main_snapshot -> fix_skill_invoke_snapshot`
3. `main_snapshot -> fix_ui_parity_snapshot`

## 本轮明确不做

- 不把 `claw-code` 代码复制进 `backend/app`
- 不重构 CarbonRag 当前 provider 层
- 不把 coding-agent CLI 当成 CarbonRag 产品壳
- 不引入 plugin、hooks、memory 的伪实现
- 不把本轮包装成“已完成集成”
