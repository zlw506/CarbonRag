# OpenSpec + Codex Workflow Runbook

版本：V1.2.5

## 核心判断

OpenSpec 不需要长期运行后台服务。它是规格和变更工作流。每轮开发时，开发者在终端运行 OpenSpec 命令，并让 Codex 读取对应 specs / changes 后再施工。

## 每轮终端流程

### 1. 同步基线

#1：

```powershell
git fetch origin
git switch main
git pull origin main
git switch -c t1/v1.2/<topic>
```

#2/#3：

```powershell
git fetch upstream
git switch -c t2/v1.2/<topic> upstream/main
```

### 2. 验证当前规格

```powershell
openspec list
openspec validate --all
```

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

### 6. 让 Codex 施工

给 Codex 的固定输入模板：

```text
先读取 AGENTS.md、openspec/AGENTS.md、openspec/specs/**、openspec/changes/<change-id>/**、docs/governance/** 和相关架构文档。
本轮 change-id: <change-id>。
先检查 proposal/design/tasks 是否完整。
不允许无 change-id 直接实现新功能。
如果 OpenSpec skill 不可自动调用，请按文档手动读取和执行。
```

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
