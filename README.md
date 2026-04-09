# CarbonRag

当前状态：`v0.2.0 report generation first closure in progress`

## 项目定位
CarbonRag 是一个面向中小企业的“双碳”政策与企业应用智能工作台。当前主线已经从“会问、会算”推进到“会产出结构化结果文档”，围绕以下能力持续演进：
- session conversation workbench
- public policy grounding
- private sample / mixed scope grounding
- calc-carbon 最小真实链路
- feedback 落库
- session 关联报告生成

## 当前阶段
- 阶段名称：`v0.2.0 报告生成首个真实闭环中`
- 当前重点：
  - ask 已支持 `public / private_sample / mixed`
  - session、单会话上下文、附件入口已落地
  - calc-carbon 已提供真实计算链路
  - ask / calc 的反馈已写入运行时数据库
  - report 已支持生成、保存、重开与重新生成
  - 云端验证链路已跑通：Netlify 前端 + VPS 后端 + `/api` 代理
  - 本地与云端继续保持双环境策略：`local-dev` 与 `cloud-stable`

## 运行模式

### local-dev
- 用途：长期开发、调试、破坏性验证
- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- 前端 API 基址：`http://127.0.0.1:8000/api`
- 后端存储：SQLite fallback
- 数据特征：本地实验数据，不与云端共享

### cloud-stable
- 用途：稳定展示、外部测试、版本验收
- 前端：Netlify
- 后端：VPS
- 前端 API 基址：`/api`
- 后端存储：PostgreSQL
- 数据特征：多端共享同一云端运行时数据库

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
- `POST /api/v1/reports`
- `POST /api/v1/generate-report`（deprecated alias）
- `GET /api/v1/reports/{report_id}`
- `PATCH /api/v1/reports/{report_id}`
- `GET /api/v1/sessions/{id}/reports`
- `GET /api/v1/sessions/{id}/carbon-calculations`

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
- 如果传入 `session_id`，结果会关联到当前 session，但不会进入 ask 消息流

## Report 能力
- 当前支持 3 类报告：
  - `policy_summary`
  - `mixed_analysis`
  - `carbon_summary`
- 每份报告都必须绑定 `session_id`
- 报告可引用：
  - 已选中的 assistant 消息
  - ask citations
  - 可选的一条 calc-carbon 结果
- 报告生成后会回写一条 `system` 消息到当前 session
- 当前支持：
  - 生成
  - 重开查看
  - 重新生成（新建一份报告）
  - 编辑并保存（覆盖当前正文）
- 当前不做：
  - docx / pdf 导出
  - 版本 diff
  - 跨会话报告聚合
  - 附件自动解析进报告

## Feedback 能力
- ask 助手消息支持赞 / 踩 + 可选备注
- calc 结果支持赞 / 踩 + 可选备注
- 反馈统一写入运行时数据库
- 本轮不做反馈列表页与管理后台

## 本地启动

### 标准本地启动
Windows：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-local.ps1
```

macOS / Linux：

```bash
bash scripts/dev-local.sh
```

### 初始化与检查
Windows：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

macOS / Linux：

```bash
bash scripts/bootstrap.sh
```

`bootstrap` 只负责安装依赖、准备模板和跑检查；真正拉起本地前后端请使用 `dev-local`。

## 发布纪律
- 本地最新开发：`feature/*`
- 云端稳定发布：`release/cloud-stable`
- 不允许把每个开发 commit 直接自动推到云端
- Netlify 生产站点默认盯 `release/cloud-stable`
- VPS 后端部署默认使用 `release/cloud-stable`

## 生产部署口径
- 后端部署目录：`/srv/carbonrag/app`
- 后端入口：`app.main:app`
- 生产环境变量文件：`/etc/carbonrag/carbonrag.env`
- 生产运行时数据库：PostgreSQL
- 生产前端：Netlify
- 生产前端 API 基址：`/api`

部署说明见：
- `docs/deploy/LOCAL_DEV_VS_CLOUD_STABLE.md`
- `docs/deploy/VPS_BACKEND_DEPLOY.md`
- `docs/deploy/NETLIFY_FRONTEND.md`
- `docs/deploy/carbonrag.service`

## 当前不做
- Netlify Functions 承载后端
- Scope 3 全量
- 多行业碳核算模板
- 自动从附件抽取活动数据
- 报告 docx / pdf 导出
- 报告版本 diff
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
- `docs/GIT_RELEASE_FLOW.md`
- `docs/TECH_STACK_BASELINE.md`
- `docs/MVP_SCOPE.md`
- `docs/DEVELOPMENT_BOOTSTRAP.md`
- `docs/API_BOUNDARY_DRAFT.md`
- `docs/PLAN/v0.1.9A.md`
- `docs/PLAN/v0.1.9C.md`
- `docs/PLAN/v0.1.9F.md`
- `docs/PLAN/v0.2.0.md`
- `docs/deploy/LOCAL_DEV_VS_CLOUD_STABLE.md`
- `docs/deploy/VPS_BACKEND_DEPLOY.md`
- `docs/deploy/NETLIFY_FRONTEND.md`
- `docs/architecture/PRIVATE_SAMPLE_RETRIEVAL_FLOW.md`
- `docs/architecture/MIXED_SCOPE_ASK_FLOW.md`
- `docs/architecture/REPORT_GENERATION_FLOW.md`
- `docs/research/claw-code/`
