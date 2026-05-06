# Governance Spec 中文说明

版本：V1.2.5

本文件是 `openspec show governance` 的中文读本。英文版 `openspec/specs/governance/spec.md` 仍是 OpenSpec 可解析的正式规格。

## governance 是什么？

`governance` 不是“当前要做的任务”。它是 CarbonRag 的协作规则规格，说明所有席位如何使用 OpenSpec、Codex、Git、PR、模块边界和发布纪律。

## 当前治理规则

### 1. 新功能必须先有 OpenSpec change

任何非平凡产品行为变更，都要先创建：

```text
openspec/changes/<change-id>/
```

并至少包含：

- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/<domain>/spec.md`

### 2. PR 必须说明模块、风险、验证和批准

进入 `main` 的 PR 必须填写模板，说明：

- OpenSpec change-id
- 影响哪些 specs
- 影响 M1-M8 哪些模块
- 是否改 API / DB / 权限 / 部署 / 模型调用
- 跑了哪些验证
- 谁批准

### 3. 协作资产必须提交

仓库必须包含每个席位都需要的协作资产：

- OpenSpec specs
- Codex skills
- governance docs
- architecture docs
- scripts
- PR template
- CODEOWNERS
- env templates
- version plans

### 4. 本地资产必须忽略并可重建

这些不提交：

- `.env`
- `node_modules`
- `.spec-gen`
- SQLite/runtime data
- uploads
- API key
- 本地模型路径

但文档必须说明如何重建。

### 5. OpenSpec + Codex 工作流必须可从终端执行

即使 Codex 客户端不能自动调用 OpenSpec skill，开发者也必须能按文档手动创建 change 文件并运行：

```powershell
openspec validate --all
```

### 6. PR 最终必须人审

Codex 可以辅助审查，但 #1 必须人工决定 approve / comment / request changes。

### 7. Codex 可以处理 Git，但必须受仓库纪律约束

Codex 可以检查和操作 Git，但必须说明意图，不能自由发挥。涉及 commit、push、merge、rebase 等状态改变时，必须按任务目标和仓库纪律执行。

### 8. CarbonRag 不重复 openspec init

本仓库已经初始化过 OpenSpec。后续只运行：

```powershell
openspec update .
openspec list
openspec validate --all
```

不要重复 `openspec init`。

### 9. OpenSpec cleanup 默认保留 CarbonRag 指令

如果 `openspec update .` 提示删除 `openspec/AGENTS.md` 或 instruction 文件，默认选 `n`，除非 #1 确认内容已经迁移。

## 和日常开发的关系

- `openspec show governance`：看协作规则。
- `openspec list`：看当前是否有活跃 change。
- `openspec show <change-id>`：看某个具体任务。
- `openspec validate --all`：确认 specs 和 changes 合法。

真正开工不是看 governance，而是创建一个 change，然后走：

```text
propose -> apply -> archive
```
