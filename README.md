# CarbonRag

当前状态：`v0.1.9C deployment config in progress`

## 项目定位
CarbonRag 是一个面向中小企业的“双碳”政策与企业应用智能问答 MVP。当前主线围绕：
- ask 对话工作台
- public policy grounding
- private sample grounding
- calc-carbon 最小真实链路
- feedback 落库

## 当前阶段
- 阶段名称：`v0.1.9C 前后端部署配置中`
- 当前重点：
  - ask 已支持 `public / private_sample / mixed`
  - session、单会话上下文、附件入口已落地
  - calc-carbon 已提供首条真实计算链路
  - ask / calc 的反馈已写入运行时数据库
  - 生产部署配置正在补齐：VPS 后端 + Netlify 前端
- 当前原则：
  - 生产后端运行时持久化统一走 PostgreSQL
  - 本地开发与测试继续保留 SQLite fallback
  - 生产前端统一通过 `/api/*` 访问后端，由 Netlify 代理到 VPS

## 当前开放接口
- `GET /healthz`
- `GET /api/v1/system/info`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{id}`
- `PATCH /api/v1/sessions/{id}`
- `POST /api/v1/sessions/{id}/ask`
- `POST /api/v1/files`
- `GET /api/v1/private-samples`
- `PUT /api/v1/sessions/{id}/attached-files/private-samples`
- `POST /api/v1/calc-carbon`
- `POST /api/v1/feedback`

## Ask 能力
- `knowledge_scope=public`：只使用本地公共政策样本
- `knowledge_scope=private_sample`：只使用当前 session 已挂接的脱敏企业样例
- `knowledge_scope=mixed`：同时参考公共政策与当前 session 已挂接的脱敏企业样例
- citations 已区分来源类型：`public_policy` / `private_sample`
- 上传文件当前只做 session 绑定与展示，不参与 ask 检索

## Calc-Carbon 能力
- 当前支持 3 类活动数据：
  - `electricity_kwh`
  - `natural_gas_m3`
  - `diesel_l`
- 返回内容包括：
  - 总排放量
  - 分项 breakdown
  - 因子来源 citations
  - 公式说明
  - `trace_id`
- 如果传入 `session_id`，结果会关联到当前 session，但不会写入 ask 消息流

## Feedback 能力
- ask 助手消息支持赞 / 踩 + 可选备注
- calc 结果支持赞 / 踩 + 可选备注
- 反馈统一写入运行时数据库
- 本轮不做反馈列表页与管理后台

## 本地启动

### 初始化
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

### 前端
```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

### 后端
```powershell
cd backend
.\.conda\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 生产部署口径
- 后端部署目录：`/srv/carbonrag/app`
- 后端入口：`app.main:app`
- 生产环境变量文件：`/etc/carbonrag/carbonrag.env`
- 生产运行时数据库：PostgreSQL
- 生产前端：Netlify
- 生产前端 API 基址：`/api`

部署说明见：
- `docs/deploy/VPS_BACKEND_DEPLOY.md`
- `docs/deploy/NETLIFY_FRONTEND.md`
- `docs/deploy/carbonrag.service`

## 当前不做
- Netlify Functions 承载后端
- Scope 3 全量
- 多行业碳核算模板
- 自动从附件抽取活动数据
- `generate-report` 真实实现
- 跨会话长期 memory
- 插件系统
- 自动知识同步
- 真实企业客户数据接入

## 文档入口
- `before_all.md`
- `docs/PROJECT_PRODUCTION_SPEC.md`
- `docs/PROJECT_POSITIONING.md`
- `docs/TEAM_AND_ROLE.md`
- `docs/GIT_WORKFLOW.md`
- `docs/TECH_STACK_BASELINE.md`
- `docs/MVP_SCOPE.md`
- `docs/DEVELOPMENT_BOOTSTRAP.md`
- `docs/API_BOUNDARY_DRAFT.md`
- `docs/PLAN/v0.1.9A.md`
- `docs/PLAN/v0.1.9C.md`
- `docs/architecture/PRIVATE_SAMPLE_RETRIEVAL_FLOW.md`
- `docs/architecture/MIXED_SCOPE_ASK_FLOW.md`
- `docs/research/claw-code/`
