# CarbonRag

当前状态：第 `v0.1.9A` 轮 `calc-carbon + feedback foundation（local-first）` 施工中。

## 项目定位
CarbonRag 是一个面向中小企业的“双碳”政策与企业应用智能问答 MVP，当前目标是围绕：

- 政策理解
- 企业脱敏样例接入
- 基础碳核算
- 后续报告生成

逐步形成首条可演示的受控产品闭环。

## 当前阶段
- 阶段名称：`v0.1.9A calc-carbon + feedback foundation`
- 当前重点：
  - ask 已支持 `public / private_sample / mixed`
  - ask 已支持 session、多轮上下文、公共政策 grounding、脱敏企业样例 grounding
  - calc-carbon 已提供首个真实本地计算链路
  - ask 与 calc 两侧都已支持反馈写入本地 SQLite
- 当前原则：
  - 本轮保持本地可用，不做 Netlify / VPS 实际上线
  - calc 这轮是“真实公式服务”，不是 LLM 推理
  - memory 目前只到 session / 单会话层
  - report、长期 memory、插件系统继续后置

## 当前已开放的接口
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

## ask 当前能力
- `knowledge_scope=public`：只使用本地公共政策样本
- `knowledge_scope=private_sample`：只使用当前 session 已挂接的脱敏企业样例
- `knowledge_scope=mixed`：同时参考公共政策与当前 session 已挂接的脱敏企业样例
- citations 已区分来源类型：`public_policy` / `private_sample`
- 当前上传文件只绑定 session 和展示，不参与 ask 检索

## calc-carbon 当前能力
- 当前仅支持 3 类活动数据：
  - `electricity_kwh`
  - `natural_gas_m3`
  - `diesel_l`
- 返回内容包括：
  - 总排放量
  - 分项 breakdown
  - 因子来源 citations
  - 公式说明
  - `trace_id`
- 结果可关联到当前 session，但本轮不会进入 ask 消息流

## feedback 当前能力
- ask 助手消息支持赞 / 踩 + 可选备注
- calc 结果支持赞 / 踩 + 可选备注
- 反馈统一写入本地运行时 SQLite
- 本轮不做反馈列表页、管理后台和审核流

## 启动方式

### 一键初始化
- Windows：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1`
- macOS / Linux：`bash scripts/bootstrap.sh`

说明：初始化脚本只负责准备环境、安装依赖和运行检查，不会常驻启动前后端。

### 手动启动前端
```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

### 手动启动后端
```powershell
cd backend
.\.conda\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

如果当前机器没有 `backend/.conda`，也可以重新创建：
```powershell
cd backend
conda create -p .conda python=3.11 -y
.\.conda\python.exe -m pip install -r requirements.txt
.\.conda\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 当前阶段不做
- Netlify / VPS / 云端挂载验证
- Scope 3 全量
- 多行业碳核算模板
- 附件自动抽取活动数据
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
- `docs/architecture/PRIVATE_SAMPLE_RETRIEVAL_FLOW.md`
- `docs/architecture/MIXED_SCOPE_ASK_FLOW.md`
- `docs/research/claw-code/`

## 仓库说明
当前仓库以本地可运行工程为基线，v0.1.x 逐步把 ask、session、public/private grounding、calc-carbon 和 feedback 推进成可演示产品链路。云端部署与后续 calc/report 深化会在下一轮继续展开。
