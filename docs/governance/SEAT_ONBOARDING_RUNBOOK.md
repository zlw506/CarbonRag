# Seat Onboarding Runbook

版本：V1.2.5

## 目标

让 #2、#3 等新席位从云端仓库开始，独立完成 clone、环境准备、本地测试和 PR 提交流程。

## 前置工具

- Git
- Node.js 22+，最低满足 OpenSpec 当前要求
- npm
- Python 3.11
- VS Code
- Codex CLI 或 VS Code Codex
- OpenSpec CLI：`npm install -g @fission-ai/openspec@latest`
- GitHub CLI：建议安装，用于 PR checkout 和 review

## #2 fork-and-PR 标准流程

1. 在 GitHub 上 fork：

```text
https://github.com/Git-ys1/CarbonRag
```

2. clone 自己的 fork：

```powershell
git clone https://github.com/<your-github-username>/CarbonRag.git
cd CarbonRag
```

3. 添加 upstream：

```powershell
git remote add upstream https://github.com/Git-ys1/CarbonRag.git
git fetch upstream
```

4. 从 upstream main 开分支：

```powershell
git switch -c t2/v1.2/onboarding-smoke upstream/main
```

5. 验证 OpenSpec：

```powershell
openspec list
openspec validate --all
```

6. 初始化依赖：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

7. 启动本地开发环境：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-local.ps1
```

8. 浏览器访问：

```text
http://127.0.0.1:5173
```

后端健康检查：

```text
http://127.0.0.1:8000/healthz
```

## 忽略文件如何恢复

| 被忽略内容 | 新席位如何获得 |
| --- | --- |
| `.env` | 从 `.env.example` 复制，填自己的本地值 |
| `frontend/.env.local` | 从 `frontend/.env.example` 复制 |
| `node_modules/` | `npm ci` 自动生成 |
| Python venv / `.conda` | bootstrap 或手动 `python -m venv .venv` |
| SQLite / runtime data | 本地启动后自动生成 |
| uploads | 本地上传文件后生成 |
| `.spec-gen/` | 需要反向分析时本地重新运行 spec-gen |
| `3rdparty/spec-gen/` | 需要时本地 clone，不作为仓库协作事实源 |

## 提交 PR 前最小检查

```powershell
openspec validate --all
cd backend
python -m pytest
cd ..\frontend
npm run typecheck
npm run build
cd ..
```

如果本机 Python 命令不同，按 `docs/DEVELOPMENT_BOOTSTRAP.md` 的 Windows 示例选择 `.conda` 或 `.venv`。

## 同步 upstream main

```powershell
git fetch upstream
git rebase upstream/main
```

遇到冲突时先解决冲突，再重新执行 OpenSpec 和测试验证。

## PR 目标

#2/#3 的 PR 目标固定为：

```text
Git-ys1/CarbonRag:main
```

PR 必须填写 `.github/PULL_REQUEST_TEMPLATE.md`。
