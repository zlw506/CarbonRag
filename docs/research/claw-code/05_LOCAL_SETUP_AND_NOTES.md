# Local Setup And Notes

## 当前样本有效性说明

### 样本来源

当前本地样本来自 `3rdparty/clone-zip/` 下的四份压缩包，并已整理为：

- `3rdparty/claw-code-study/main_snapshot/`
- `3rdparty/claw-code-study/fix_plugin_loading_parity_snapshot/`
- `3rdparty/claw-code-study/fix_skill_invoke_snapshot/`
- `3rdparty/claw-code-study/fix_ui_parity_snapshot/`

### 当前样本性质

- 当前样本是静态目录快照
- 当前样本不含 `.git` 元数据
- 当前样本可用于架构研究、目录对照、关键文件对照
- 当前样本不可用于 branch history、commit history、merge-base 分析

## 快照根目录确认

| 快照 | README | CLAW | PARITY | rust | src | tests | .git |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `main_snapshot` | yes | yes | yes | yes | yes | yes | no |
| `fix_plugin_loading_parity_snapshot` | yes | yes | yes | yes | yes | yes | no |
| `fix_skill_invoke_snapshot` | yes | yes | yes | yes | yes | yes | no |
| `fix_ui_parity_snapshot` | yes | yes | yes | yes | yes | yes | no |

## 当前研究能做什么

- 阅读 README / CLAW / PARITY 的自我定义
- 阅读 Rust workspace 和 `src/` 目录面
- 对同路径文件做目录级 diff
- 输出 adoption matrix

## 当前研究不能做什么

- 声称做了 git 分支历史研究
- 声称做了 commit 级演化分析
- 声称做了真实 branch merge 关系验证
- 把静态快照当成 CarbonRag 可直接依赖的第三方组件

## 本轮差异热点

### main vs fix_plugin_loading_parity_snapshot

- 主要集中在 `rust/crates/commands/src/lib.rs`
- 主要集中在 `rust/crates/tools/src/lib.rs`
- 主要集中在 `rust/crates/plugins/src/lib.rs`

### main vs fix_skill_invoke_snapshot

- 主要集中在 `rust/crates/commands/src/lib.rs`
- 主要集中在 `rust/crates/tools/src/lib.rs`
- 主要集中在 `rust/crates/claw-cli/src/main.rs`

### main vs fix_ui_parity_snapshot

- 主要集中在 `rust/crates/claw-cli/src/input.rs`
- 主要集中在 `rust/crates/claw-cli/src/main.rs`
- 主要集中在 `rust/crates/runtime/src/skills.rs`
- 主要集中在 `README.md` 与 `PARITY.md`

## Rust 本地验证

### 安装路径

- 计划使用官方 `rustup-init.exe`
- 本机存在 Visual Studio Build Tools，可走 stable MSVC toolchain
- Visual Studio Build Tools 路径：`F:\CodeForge\Microsoft Visual Studio\18\BuildTools`
- 本轮实际安装结果：
  - `rustup 1.29.0`
  - `rustc 1.94.1`
  - `cargo 1.94.1`

### 验证命令

在 `main_snapshot/rust` 下执行：

```powershell
cargo build --release
cargo fmt --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

### 本轮结果

- `cargo build --release`：通过
- `cargo fmt --check`：失败
  - 失败性质：主快照自身存在未格式化代码
  - 典型位置：`crates/lsp/src/client.rs`、`crates/lsp/src/lib.rs`、`crates/lsp/src/manager.rs`、`crates/runtime/src/lib.rs`、`crates/tools/src/lib.rs`
- `cargo clippy --workspace --all-targets -- -D warnings`：失败
  - 失败性质：主快照自身存在 warning，在 `-D warnings` 下被提升为错误
  - 首个明确错误：`crates/plugins/src/hooks.rs` 中 `use std::path::Path;` 未使用
- `cargo test --workspace`：失败
  - 失败性质：Windows/MSVC 下命中 Unix 专用测试代码
  - 典型位置：`crates/runtime/src/mcp_stdio.rs`
  - 典型报错：`std::os::unix::fs::PermissionsExt` 不存在、`Permissions::set_mode` 不可用

## 当前结论

主快照在本机 Windows + stable MSVC 环境下具备以下状态：

- 可以完成 release build
- 不能通过严格格式检查
- 不能通过 `-D warnings` 的 clippy 检查
- 不能直接通过全量 workspace 测试

这说明当前样本是“活的、可编译的”，但不是“在本机完全绿色”的状态。

## 后续若要补 git 元数据

若后续开启 `v0.1.3C`，应补正为：

1. 获取可访问的真实仓库地址
2. 完整 `git clone`
3. 拉取目标分支
4. 在真实 `.git` 元数据上做 branch / file / commit 级 diff
