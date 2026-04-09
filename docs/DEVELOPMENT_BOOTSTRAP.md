# Development Bootstrap
版本：v0.1.9F

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
- `PUBLIC_DATA_DIR` / `PRIVATE_SAMPLE_DIR` / `FACTOR_DATA_DIR` 指向仓库内 `data/`

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
- 本地历史记录与云端历史记录不共享
- ask / calc / feedback 已可本地联调
- 共享云端环境不承担日常 feature 半成品验证
