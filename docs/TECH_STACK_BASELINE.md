# 技术栈基线
版本：v0.0.2

## 前端
React + TypeScript + Vite + Ant Design + React Router + Axios

## 后端
Python 3.11 + FastAPI + Uvicorn

## 模型层
第三方云端 API，统一封装，不写死供应商；本轮仅保留 provider 抽象壳与 `cloud_api_stub`

## 数据层
data/public
data/private_sample
data/factors
data/outputs

## 环境变量
- 根目录 `.env.example`：后端私有配置模板
- `frontend/.env.example`：前端公开配置模板
- 不提交真实 key，不把模型密钥暴露到前端
