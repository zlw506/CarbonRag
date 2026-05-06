# Open Collaboration Guide Test Report

版本：V1.2.5

## 测试环境

- 工作目录：`F:\Project\CarbonRag`
- 分支：`t1/v1.2/openspec-governance-baseline`
- Node.js：`v24.11.0`
- npm：`11.6.1`
- OpenSpec：`1.3.1`
- GitHub CLI：`2.90.0`
- VS Code：`1.118.1`
- VS Code GitHub Pull Requests 扩展：`github.vscode-pull-request-github`，已安装 `0.142.0`

## OpenSpec 测试

已执行：

```powershell
openspec list
openspec validate --all
```

结果：

- `openspec list`：No active changes found
- `openspec validate --all`：8 specs passed, 0 failed

## 忽略规则测试

已执行：

```powershell
git check-ignore -v .spec-gen/test.txt
git check-ignore -v 3rdparty/spec-gen/test.txt
git check-ignore -v .env
```

结果：

- `.spec-gen/test.txt` 被 `.gitignore` 的 `.spec-gen/` 命中。
- `3rdparty/spec-gen/test.txt` 被 `.gitignore` 的 `/3rdparty/*` 命中。
- `.env` 被 `.gitignore` 的 `.env` 命中。

## GitHub CLI 测试

已安装 GitHub CLI 便携版到用户目录，并写入用户 PATH。

已执行：

```powershell
gh --version
gh auth status
gh pr list
```

结果：

- `gh --version`：`gh version 2.90.0 (2026-04-16)`
- `gh auth status`：已登录 `github.com`，账号 `Git-ys1`，Git protocol 为 `https`
- `gh pr list`：命令执行成功，当前列表为空

说明：GitHub CLI 已可用于后续 `gh pr checkout`、`gh pr review` 和 PR 列表检查。

## VS Code PR 扩展测试

已执行：

```powershell
F:\CodeForge\Microsoft VS Code\bin\code.cmd --version
F:\CodeForge\Microsoft VS Code\bin\code.cmd --install-extension GitHub.vscode-pull-request-github --force
F:\CodeForge\Microsoft VS Code\bin\code.cmd --list-extensions
```

结果：

- VS Code CLI 可用。
- GitHub Pull Requests 扩展安装成功。
- 扩展列表中可见 `github.vscode-pull-request-github`。

## Bootstrap / Test 测试

已执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -SkipInstall
```

结果：

- 前端 `npm run typecheck` 通过。
- 前端 `npm run build` 通过，存在既有 chunk size warning。
- 后端 pytest 通过：`106 passed, 4 warnings`。

说明：`dev-local.ps1` 是长运行启动脚本，会打开前后端窗口。本轮未在自动化验证中长期拉起服务，以避免留下后台进程；新席位按 `SEAT_ONBOARDING_RUNBOOK.md` 执行即可。

## 本地协作资产清点

当前未忽略文件处理策略：

- 已暂存 V1.1.x 计划文档和 UX 审查文档：纳入 V1.2.5 发布。
- `backend/app/ai_runtime/tools/enterprise_retrieve_stub.py`：已检查，不含密钥、本地路径或临时垃圾，纳入 V1.2.5 发布。
- `.spec-gen/`、`3rdparty/spec-gen/`、`.env`、runtime data、node_modules、backend `.conda`：继续忽略。

## 结论

#2 可以从 `main` fork/clone 后完成本地测试。被忽略文件不是协作缺口，而是每台机器根据模板、脚本和依赖安装重建的本地状态。
