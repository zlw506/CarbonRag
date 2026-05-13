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
用于后端本地开发配置。当前 V1.6.x 本地默认值是：
- `APP_ENV=development`
- `DATABASE_URL=` 为空，避免误连云端 PostgreSQL
- `MEMORY_BACKEND=sqlite`
- `AI_CHAT_PROVIDER=ollama`、`OLLAMA_BASE_URL=http://localhost:11434`、`OLLAMA_MODEL=deepseek-r1:8b`，local-dev 默认走本机 Ollama native API；如没有本地模型，先按 `docs/architecture/LOCAL_LLM_RUNTIME_PROFILES.md` 配置。
- `RAG_ENGINE_ENABLED=true`、`RAG_VECTOR_ENABLED=true`、`RAG_VECTOR_BACKEND=milvus`、`RAG_MILVUS_URI=http://127.0.0.1:19530`，Windows 默认使用 Docker Milvus Standalone。
- `PUBLIC_DATA_DIR` / `PRIVATE_SAMPLE_DIR` / `FACTOR_DATA_DIR` 指向仓库内 `data/`

V1.6.x 的 BGE-M3 / reranker 模型包与本地聊天模型包不进入 Git：

```text
data/outputs/models/BAAI/bge-m3
data/outputs/models/BAAI/bge-reranker-v2-m3
data/outputs/models/LLM/<model-name>
```

V1.6.17 的 Ollama smoke：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/llm-ollama-smoke.ps1
```

注意：Netlify + VPS 云端后端默认不能访问开发者电脑的 `localhost:11434`。本地 Ollama 能力只保证 `local-dev`；云端要用本地模型，必须另行部署可被 VPS 访问的远程 Ollama endpoint。

### V1.6 RAG-Pro 本地验证开关

V1.6 的 RAG-Pro 主脊柱默认要求真实向量链路。Windows 开发者需先启动 Docker Desktop 和 Milvus Standalone：

```env
RAG_ENGINE_ENABLED=true
RAG_VECTOR_ENABLED=true
RAG_VECTOR_BACKEND=milvus
RAG_MILVUS_URI=http://127.0.0.1:19530
RAG_REQUIRE_REAL_VECTOR=true
```

`memory` 只允许 UI/API 开发降级，不允许作为 RAG-Pro 验收。

### Legacy RAG Lab 本地验证

该入口仅保留给管理员排查旧 `/rag/retrieve`、BM25、graph_mode 等实验参数，不参与 V1.6.x RAG-Pro 验收。正式验收请使用“知识库工作台”、AskPage、`/api/v1/rag/search`、`/api/v1/rag/answer`、`/api/v1/rag/test-qa` 和 `/api/v1/rag/eval/run`。

管理员本地登录后可打开：

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
