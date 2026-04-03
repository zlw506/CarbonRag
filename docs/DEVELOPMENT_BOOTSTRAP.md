# Development Bootstrap
版本：v0.0.2

## 目标

本文件用于定义 CarbonRag 在稳定配置轮的最小开发启动流程。当前目标不是进入业务开发，而是确保新成员可以稳定安装依赖、启动前端与后端最小服务，并跑通基础检查。

## 环境基线

- Node.js：建议 `22+`，当前本地验证环境为 `24.x`
- npm：跟随 Node.js 默认安装
- Python：固定使用 `3.11`
- Git：要求可正常推送 `dev` 与 `feature/*` 分支

## 一键脚本

### Windows

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

### macOS / Linux

```bash
bash scripts/bootstrap.sh
```

脚本行为：

1. 若根目录 `.env` 不存在，则从 `.env.example` 复制
2. 若 `frontend/.env` 不存在，则从 `frontend/.env.example` 复制
3. 安装前端依赖
4. 创建后端虚拟环境并安装依赖
5. 运行前端类型检查与构建检查
6. 运行后端 pytest 最小测试
7. 打印后续启动命令

## 手动启动

### 前端

```bash
cd frontend
npm install
npm run dev
```

默认访问地址：

- `http://127.0.0.1:5173`

### 后端

优先方案：

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

若当前机器的 `py -3.11` 不可用，但已安装 conda，可使用回退方案：

```powershell
cd backend
conda create -p .conda python=3.11 -y
.\.conda\python.exe -m pip install -r requirements.txt
.\.conda\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

默认访问地址：

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/api/v1/system/info`

## 环境变量说明

### 根目录 `.env`

只用于后端私有配置。允许包含：

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `MODEL_API_BASE_URL`
- `MODEL_API_KEY`
- `MODEL_NAME`
- `EMBEDDING_API_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `VECTOR_STORE_PATH`
- `PUBLIC_DATA_DIR`
- `PRIVATE_SAMPLE_DIR`
- `FACTOR_DATA_DIR`

### `frontend/.env`

只允许浏览器可见配置：

- `VITE_API_BASE_URL`
- `VITE_APP_TITLE`

禁止把任何模型密钥或第三方模型供应商配置放进前端环境变量。

## 最小检查命令

### 前端

```bash
cd frontend
npm run typecheck
npm run build
```

### 后端

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests
```

若使用 conda 回退方案：

```powershell
cd backend
.\.conda\python.exe -m pytest tests
```

## 当前边界

- 当前未实现 ask、calc-carbon、generate-report 业务逻辑
- 当前前端只允许调用后端最小接口
- 当前后端 provider 仅为抽象壳与 stub
- 当前数据目录只允许公开样本、脱敏样例和说明文档
