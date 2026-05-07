# Development Bootstrap
版本：V1.2.5

## 目标
本文件用于定义 CarbonRag 的本地初始化和检查流程。当前仓库已经固定为双环境模式：
- `local-dev`：本地最新开发环境
- `cloud-stable`：云端稳定验证环境

`bootstrap` 只负责准备本地依赖与检查，不负责启动前后端服务。

## 环境基线
- Node.js：建议 `22+`
- npm：跟随 Node.js
- Python：固定 `3.11`
- Git：需要可正常推送 `feature/*` 与 `release/cloud-stable`
- OpenSpec CLI：建议全局安装 `@fission-ai/openspec`

## 新席位从云端开始

#2/#3 不需要任何 #1 本机的被忽略文件。标准入场方式是：

```powershell
git clone https://github.com/<your-github-username>/CarbonRag.git
cd CarbonRag
git remote add upstream https://github.com/Git-ys1/CarbonRag.git
git fetch upstream
git switch -c t2/v1.2/onboarding-smoke upstream/main
openspec list
openspec validate --all
```

被忽略的 `.env`、`frontend/.env.local`、依赖目录、SQLite、uploads 和 `.spec-gen/` 都是本地状态，可由模板、脚本或本地命令重建。

## 初始化脚本

### Windows
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

### macOS / Linux
```bash
bash scripts/bootstrap.sh
```

## bootstrap 行为
1. 若根目录 `.env` 不存在，则从 `.env.example` 复制
2. 安装前端依赖
3. 创建后端 Python 环境并安装依赖
4. 运行前端类型检查与生产构建检查
5. 运行后端 pytest
6. 打印后续本地启动方式

注意：
- `bootstrap` 不再生成 `frontend/.env`
- 本地前端环境文件改为 `frontend/.env.local`
- 真正拉起本地前后端请使用 `scripts/dev-local.ps1` 或 `scripts/dev-local.sh`

如果 bootstrap 在新机器上失败，先记录：

```powershell
node --version
npm --version
python --version
git --version
openspec --version
```

然后按错误定位缺失依赖，不要把本地生成目录提交到仓库。

## 标准本地启动

### Windows
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-local.ps1
```

### macOS / Linux
```bash
bash scripts/dev-local.sh
```

`dev-local` 会：
- 确保 `frontend/.env.local` 存在
- 确保根目录 `.env` 存在
- 启动本地后端 `127.0.0.1:8000`
- 启动本地前端 `127.0.0.1:5173`
- 强制本地后端走 SQLite fallback

## 环境变量口径

### 根目录 `.env`
用于后端本地开发配置。当前本地安全默认值是：
- `APP_ENV=development`
- `DATABASE_URL=` 为空，避免误连云端 PostgreSQL
- `MEMORY_BACKEND=sqlite`
- `RAG_ENGINE_ENABLED=false`、`RAG_VECTOR_ENABLED=false`、`RAG_RERANK_ENABLED=false`，默认保留现有 BM25 检索 fallback
- `PUBLIC_DATA_DIR` / `PRIVATE_SAMPLE_DIR` / `FACTOR_DATA_DIR` 指向仓库内 `data/`

### V1.3 RAG 实验开关

V1.3 的 LightRAG-style RAG 骨架是安全默认关闭的。未配置向量、图谱、embedding 或 rerank 后端时，后端仍应启动并继续使用现有 public/private/mixed BM25 检索。

```env
RAG_ENGINE_ENABLED=false
RAG_VECTOR_ENABLED=false
RAG_RERANK_ENABLED=false
RAG_DEFAULT_MODE=mix
```

含义：
- `RAG_ENGINE_ENABLED`：启用新的内部 RAG engine 边界；关闭时只记录 fallback metadata。
- `RAG_VECTOR_ENABLED`：允许 RAG engine 尝试向量 chunk 检索；关闭时走 BM25 fallback。
- `RAG_RERANK_ENABLED`：允许 RAG engine 调用 M1 rerank provider；当前默认 provider 为 disabled。
- `RAG_DEFAULT_MODE`：内部检索模式，当前只接受 `naive` 和 `mix`，异常值会回退到 `mix`。

### V1.3 RAG Lab 本地验证

本地登录后可打开：

```text
http://127.0.0.1:5173/rag-lab
```

对应后端接口：

```text
POST http://127.0.0.1:8000/api/v1/rag/retrieve
```

可验证项：
- 切换 `Mix` / `Naive`，确认返回 metadata 中的 `mode` 和 graph 状态变化。
- 切换公共 / 知识条目 / 混合范围，确认证据片段来源和 references 变化。
- 调整返回条数、候选片段、rerank 开关，确认 metadata 中 `top_k`、`chunk_top_k`、`rerank_status` 变化。
- 在默认关闭 RAG 向量开关时，确认页面显示 `rag_engine_disabled` 或 `rag_vector_disabled` fallback，同时仍返回 BM25 片段。

### `frontend/.env.local`
仅用于本地开发，默认应为：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_APP_TITLE=CarbonRag Conversation Workbench
```

### `frontend/.env.production`
仅用于生产构建，仓库内已固定为：

```env
VITE_API_BASE_URL=/api
VITE_APP_TITLE=CarbonRag Conversation Workbench
```

## 最小检查命令

### 前端
```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run build
```

### 后端
```powershell
cd backend
.\.conda\python.exe -m pytest tests
```

如果本机使用 `.venv`：
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests
```

## 当前边界
- 本地开发默认不连接云端 PostgreSQL
- 本地 memory / session 默认走 SQLite fallback
- 本地历史记录与云端历史记录不共享
- ask / calc / feedback 已可本地联调
- 共享云端环境不承担日常 feature 半成品验证

## OpenSpec 最小检查

每轮开工前执行：

```powershell
openspec list
openspec validate --all
```

新功能必须先有 `openspec/changes/<change-id>/`。如果 Codex 无法自动调用 OpenSpec skill，按 `docs/governance/OPENSPEC_CODEX_WORKFLOW_RUNBOOK.md` 手动创建 proposal/design/tasks/delta spec。
