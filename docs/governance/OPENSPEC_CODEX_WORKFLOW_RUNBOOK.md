# OpenSpec + Codex Workflow Runbook

版本：V1.2.5

## 核心判断

OpenSpec 不需要长期运行后台服务。它是规格和变更工作流。Codex 是执行者，可以处理 Git、OpenSpec、检查和提交，但必须按仓库纪律执行，不能自由发挥。

CarbonRag 已经是 brownfield 项目，已经有 `openspec/config.yaml` 和 `openspec/specs/**`。因此：

- 不要重复执行 `openspec init`。
- 当前工作区首次打通使用 `openspec update .`、`openspec list`、`openspec validate --all`。
- 如果 `openspec update .` 提示删除 `openspec/AGENTS.md`，默认回答 `n`，直到 #1 确认内容已迁移。

## 唯一开工口令

以后不要先手工拼一堆 Git 命令。把下面这段发给 Codex，让 Codex 按仓库规则检查并执行：

```text
执行本轮 OpenSpec 开工检查。
你可以处理 Git 和 OpenSpec，但必须遵守 AGENTS.md、openspec/AGENTS.md、openspec/specs/**、docs/governance/**。
先检查当前工作区、当前分支、远端状态、OpenSpec 状态和未忽略文件。
不要重复 openspec init。
如需运行 openspec update .，遇到删除 openspec/AGENTS.md 或 instruction 文件的提示，默认选择 n。
先输出你准备执行的 Git/OpenSpec 步骤；只有安全的只读检查可以直接执行。
涉及 commit、push、merge、rebase、删除、reset 的操作，必须说明原因和目标后再执行。
本轮 change-id: <change-id>。
本轮目标: <一句话目标>。
先 propose，不要直接 apply。
```

这段口令的意思不是让 AI 乱跑 Git，而是让 AI 按当前仓库规则接管重复性检查、建 change、读 specs、生成提案和后续验证。

## 每轮流程

### 1. Codex 先检查

Codex 先执行或建议：

```powershell
git status -sb
git branch --show-current
openspec list
openspec validate --all
```

如果任务需要同步远端，Codex 可以执行只读：

```powershell
git fetch origin
```

是否切分支、提交、推送，由 Codex 根据任务目标提出并执行，但必须遵守 PR 和 main 纪律。

### 2. 刷新 OpenSpec 指令

```powershell
openspec update .
openspec list
openspec validate --all
```

如果 `openspec update .` 提示清理 `openspec/AGENTS.md`，默认选 `n`。

### 3. 创建 change

优先使用 OpenSpec CLI 或 Codex skill。如果不可用，手动创建：

```text
openspec/changes/<change-id>/proposal.md
openspec/changes/<change-id>/design.md
openspec/changes/<change-id>/tasks.md
openspec/changes/<change-id>/specs/<domain>/spec.md
```

### 4. 编写 proposal

至少写清：

- 为什么要改
- 改什么
- 不改什么
- 影响模块
- 验收方式

### 5. validate change

```powershell
openspec validate <change-id> --strict
```

若 CLI 对单个 change 的命令格式因版本不同失败，执行：

```powershell
openspec validate --all
```

并把失败原因写入 PR。

### 6. 让 Codex propose

给 Codex 的固定输入模板：

```text
先读取 AGENTS.md、openspec/AGENTS.md、openspec/specs/**、openspec/changes/<change-id>/**、docs/governance/** 和相关架构文档。
本轮 change-id: <change-id>。
先生成或检查 proposal/design/tasks/delta spec。
生成后停止，等待 #1 审查。
不允许无 change-id 直接 apply。
如果 OpenSpec skill 不可自动调用，请按文档手动读取和执行。
```

### 7. 审查通过后 apply

只有 proposal/design/tasks/delta spec 审查通过后，才让 Codex apply。apply 阶段仍然要按 tasks 执行，并在每个高风险 Git 操作前说明目的。

## Codex 只读审查模板

```text
你现在只做只读审查，不改代码。
请读取 AGENTS.md、openspec/specs/**、docs/governance/**、.github/PULL_REQUEST_TEMPLATE.md、.github/CODEOWNERS。
请审查 origin/main...HEAD 的 diff，判断：
1. 是否有 OpenSpec change-id
2. 是否越过模块边界
3. 是否修改 API / DB / 权限 / 部署 / 模型调用
4. 是否缺测试或缺文档
5. 应该 approve、comment 还是 request changes
输出审查报告。
```

## 什么时候 archive

当一个 change 已经实现、测试通过、PR 合并，才执行 archive/sync。未实现或只处于 proposal 的 change 留在 `openspec/changes/**`。

## spec-gen 的位置

spec-gen 只用于 brownfield baseline draft：

- 可本地 clone 到 `3rdparty/spec-gen`
- 输出在 `.spec-gen/`
- 生成内容必须人工校验
- 不提交 `.spec-gen/` 或 `3rdparty/spec-gen/`
- 最终事实源仍是 `openspec/specs/**`
