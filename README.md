# CarbonRag

当前状态：第 0.0.2 轮稳定配置中。

## 项目定位
CarbonRag 是一个面向中小企业的“双碳”政策与企业应用智能问答 MVP，目标是围绕政策理解、企业样例接入、基础碳核算和报告生成形成首条可演示闭环。

## 当前阶段
- 阶段名称：稳定配置轮（Stable Bootstrap）
- 当前策略：统一使用第三方云端 API，保留后续替换为本地或私有模型的接口能力
- 当前默认模型：`gpt-5.4`
- 当前原则：先冻结工程壳、配置、接口边界和检查流程，再进入功能施工

## 当前已开放的最小服务
- 后端最小接口：`GET /healthz`
- 后端系统信息：`GET /api/v1/system/info`
- 前端最小页面：问答页、碳核算页、报告生成页、管理占位页

## 启动方式

### 一键启动

- Windows：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1`
- macOS / Linux：`bash scripts/bootstrap.sh`

### 手动启动前端

```bash
cd frontend
npm install
npm run dev
```

### 手动启动后端

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

若当前机器没有可用的 `py -3.11`，可改用 conda 回退：

```powershell
cd backend
conda create -p .conda python=3.11 -y
.\.conda\python.exe -m pip install -r requirements.txt
.\.conda\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 当前阶段不做
- 本地开源大模型正式部署
- 微调链路与量化部署
- 复杂权限系统与多租户体系
- 全国政策全量自动更新
- 生产级监控、审计与复杂流程编排
- ask / calc-carbon / generate-report 真实业务逻辑实现

## 文档入口
- `before_all.md`：项目立项前总纲与开工纪律
- `docs/PROJECT_PRODUCTION_SPEC.md`：第 0 轮生产规范主文档
- `docs/PROJECT_POSITIONING.md`：项目定位
- `docs/TEAM_AND_ROLE.md`：团队角色与责任边界
- `docs/GIT_WORKFLOW.md`：分支与提交纪律
- `docs/TECH_STACK_BASELINE.md`：技术栈冻结口径
- `docs/MVP_SCOPE.md`：当前阶段做与不做
- `docs/DEVELOPMENT_BOOTSTRAP.md`：稳定配置轮启动说明
- `docs/API_BOUNDARY_DRAFT.md`：下一轮接口草案

## 仓库说明
本仓库当前已进入稳定配置轮，包含可运行的前端与后端工程壳、环境变量拆分、最小检查流程和最小接口。后续开发必须基于 `dev` 或 `feature/*` 分支推进，并持续遵守文档中定义的边界与提交纪律。
