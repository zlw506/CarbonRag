# CarbonRag

当前状态：第 0.1.8 轮 enterprise-private-sample 接入中。

## 项目定位
CarbonRag 是一个面向中小企业的“双碳”政策与企业应用智能问答 MVP，目标是围绕政策理解、企业样例接入、基础碳核算和报告生成形成首条可演示闭环。

## 当前阶段
- 阶段名称：enterprise-private-sample
- 当前阶段重点：在 conversation workbench 上接入脱敏企业样例检索，并让 ask 支持 `public / private_sample / mixed`
- 当前策略：统一使用第三方云端 API，保留后续替换为本地或私有模型的接口能力
- 当前默认模型：`gpt-5.4`
- 当前原则：ask 已支持 public policy grounding、private sample retrieval 和 mixed citations；private sample 当前仅为脱敏演示样例；calc / report 继续后置；memory 当前只到 session / 单会话层

## 当前已开放的最小服务
- 后端最小接口：`GET /healthz`
- 后端系统信息：`GET /api/v1/system/info`
- 后端会话接口：`POST /api/v1/sessions`、`GET /api/v1/sessions`、`GET /api/v1/sessions/{id}`、`PATCH /api/v1/sessions/{id}`
- 后端问答接口：`POST /api/v1/sessions/{id}/ask`
- 后端文件入口：`POST /api/v1/files`
- 后端 private sample 接口：`GET /api/v1/private-samples`、`PUT /api/v1/sessions/{id}/attached-files/private-samples`
- 前端最小页面：问答工作台、碳核算页占位、报告生成页占位、管理占位页
- 后端内部 AI Runtime：`app.ai_runtime.runtime.orchestrator.run()` 已承接 ask mode 的 session history + scope-aware retrieval + provider 回答流程

## ask 当前能力
- `knowledge_scope=public`：只使用本地公共政策样本
- `knowledge_scope=private_sample`：只使用当前 session 已挂接的脱敏企业样例
- `knowledge_scope=mixed`：同时参考公共政策样本与当前 session 已挂接的脱敏企业样例
- citations 已区分来源类型：`public_policy` / `private_sample`
- 当前上传文件只绑定 session 并展示，不参与 ask 检索

## 启动方式

### 一键初始化

- Windows：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1`
- macOS / Linux：`bash scripts/bootstrap.sh`

说明：这两个脚本只负责准备环境、安装依赖和运行检查，不会常驻启动前后端开发服务。

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
- 真实企业客户数据接入
- `calc-carbon` / `generate-report` 真实业务逻辑实现
- 跨会话长期 memory、插件系统与语音输入真实链路
- 自动爬虫、完整向量数据库平台与多工具自动规划
- 上传文件深度解析与附件驱动问答

## 文档入口
- `before_all.md`：项目立项前总纲与开工纪律
- `docs/PROJECT_PRODUCTION_SPEC.md`：第 0 轮生产规范主文档
- `docs/PROJECT_POSITIONING.md`：项目定位
- `docs/TEAM_AND_ROLE.md`：团队角色与责任边界
- `docs/GIT_WORKFLOW.md`：分支与提交纪律
- `docs/TECH_STACK_BASELINE.md`：技术栈冻结口径
- `docs/MVP_SCOPE.md`：当前阶段做与不做
- `docs/DEVELOPMENT_BOOTSTRAP.md`：稳定配置轮启动说明
- `docs/API_BOUNDARY_DRAFT.md`：接口边界草案
- `docs/architecture/`：AI Runtime、session、public/private retrieval 相关架构文档
- `docs/architecture/PUBLIC_POLICY_RETRIEVAL_FLOW.md`：v0.1.6 公共政策检索接入流
- `docs/architecture/SESSION_FOUNDATION_FLOW.md`：v0.1.7 会话与上传骨架流
- `docs/architecture/PRIVATE_SAMPLE_RETRIEVAL_FLOW.md`：v0.1.8 private sample 检索流
- `docs/architecture/MIXED_SCOPE_ASK_FLOW.md`：v0.1.8 mixed scope ask 流
- `docs/PLAN/v0.1.8.md`：enterprise-private-sample 接入计划
- `docs/research/claw-code/`：第三方架构学习与 adoption / session-memory mapping

## 仓库说明
本仓库当前保留 v0.0.2 的可运行工程壳，并在 v0.1.x 逐步把 ask 推进为可演示产品链路。当前 ask 已支持 session history、public policy grounding、private sample retrieval 和 mixed scope citations。private sample 仍然只是仓库内的脱敏演示样例；calc、report、长期 memory 和插件系统仍继续后置。
