# Mattermost Watcher + Codex Wake Bridge

版本：V1.4.7C 草案

## 结论

当前 Codex 不能可靠地让外部脚本把文本直接塞进“已经打开的这个聊天输入框”。不要用模拟键盘、剪贴板、屏幕点击这类脆弱方案作为团队基础设施。

可落地方案是：

```text
Mattermost 新 PLAN / BLOCK / REVIEW_READY
-> 本机 watcher 轮询发现
-> 终端提示和蜂鸣
-> 可选调用 codex resume --last
-> Codex 恢复最近一次记录会话并带入提示词
-> #1 人类决定是否审查、approve、request changes 或 merge
```

这不是完全无人值守自动合并。#1 仍保留最终决定权。

## 前置环境

PowerShell 环境变量：

```powershell
$env:MATTERMOST_URL="http://8.141.111.33:8065"
$env:MATTERMOST_TEAM="carbonrag"
$env:MATTERMOST_TOKEN="<t1-codex PAT>"
```

不要把 PAT 写进仓库。

## 首次启动

首次运行默认只初始化当前最新消息，不回放历史，避免旧消息触发一堆提示：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/coordination/watch-mattermost.ps1 -Once
```

确认 `coordination.local.json` 已生成。该文件是本地状态文件，已被 `.gitignore` 忽略。

## 持续监听

只提示，不启动 Codex：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/coordination/watch-mattermost.ps1
```

发现 #2 的 `PLAN`、`BLOCK`、`REVIEW_READY` 后，脚本会在终端显示消息并蜂鸣。

每次触发都会写入本地交接文件：

```text
logs/coordination/latest-trigger.md
logs/coordination/<timestamp>-<channel>-<type>.md
```

这些文件是本地运行痕迹，已被 `.gitignore` 忽略。它们的作用是把“刚才 Mattermost 触发了什么”稳定保存下来，方便 #1 人类或 Codex 接管，不依赖终端滚动历史。

## 尝试唤醒 Codex

带 `-LaunchCodexResume` 后，脚本会尝试打开一个 PowerShell 窗口并执行：

```powershell
codex resume --last "<Mattermost 触发摘要>"
```

命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/coordination/watch-mattermost.ps1 -LaunchCodexResume
```

注意：

- 这会恢复最近一次 Codex 记录会话。
- 它不保证能把消息注入已经打开的 UI 输入框。
- 如果同时开了多个 Codex 会话，`--last` 可能不是你正在看的窗口。
- 高风险动作仍必须由 #1 人类确认。

## 尝试自动生成只读审查

如果触发类型是 `REVIEW_READY`，可以让 watcher 额外打开一个非交互式 Codex 只读审查窗口：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/coordination/watch-mattermost.ps1 `
  -LaunchCodexExecReview
```

或同时开启 resume：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/coordination/watch-mattermost.ps1 `
  -LaunchCodexResume `
  -LaunchCodexExecReview
```

`-LaunchCodexExecReview` 会把审查结果写到：

```text
logs/coordination/<timestamp>-codex-review-output.md
```

注意：

- 这个模式只允许 Codex 做只读审查建议。
- 不允许自动 approve、merge、push 或改文件。
- 它可能消耗额度，因此默认关闭。
- 如果要正式 approve / request changes，仍由 #1 在当前会话或 GitHub CLI 中明确执行。

## 回放最新消息测试

需要测试触发效果时可用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/coordination/watch-mattermost.ps1 -Once -ReplayLatest
```

如不想忽略 #1 自己的消息，可覆盖忽略列表：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/coordination/watch-mattermost.ps1 -Once -ReplayLatest -IgnoreUsernames @()
```

## 默认监听规则

默认频道：

- `carbonrag-control`
- `carbonrag-review`

默认触发类型：

- `PLAN`
- `BLOCK`
- `REVIEW_READY`

默认忽略用户：

- `t1-director`
- `t1-codex`

原因：#1 watcher 主要用于发现 #2/#3 需要处理的消息，不应该被 #1 自己的公告和决策反复唤醒。

## 风险边界

不允许 watcher 自动执行：

- `gh pr merge`
- `gh pr review --approve`
- `git push`
- 业务代码修改
- 数据库迁移

这些动作仍由 Codex 在被唤醒后按 OpenSpec、GitNexus、Mattermost 和 #1 指令执行。

## 后续增强

可以在下一轮补：

- Windows 计划任务自启动。
- 系统托盘通知。
- 只监听指定 PR 号。
- 将 REVIEW_READY 自动转成本地审查 checklist。
- watcher 发现 BLOCK 后自动向 `carbonrag-control` 回复 ACK。
