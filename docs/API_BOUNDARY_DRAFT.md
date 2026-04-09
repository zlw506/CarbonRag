# API Boundary Draft

版本：`v0.2.0`  
状态：`report generation first closure`

## 已开放的基础接口

### `GET /healthz`
用途：
- 提供最小健康检查
- 验证 FastAPI 服务已正常启动

成功响应：
```json
{
  "status": "ok"
}
```

### `GET /api/v1/system/info`
用途：
- 提供前端可读取的最小系统信息
- 验证 API 前缀、配置层和 provider 已接通

成功响应草案：
```json
{
  "app_name": "CarbonRag",
  "version": "v0.2.0",
  "env": "development",
  "api_prefix": "/api/v1",
  "model_provider_mode": "openai_compatible",
  "timestamp": "2026-04-09T12:00:00+08:00"
}
```

## Session 与附件接口

### `POST /api/v1/sessions`
状态：`implemented`

用途：
- 创建新的对话会话
- 为 ask、多轮上下文、calc 关联和报告生成提供主容器

### `GET /api/v1/sessions`
状态：`implemented`

用途：
- 列出所有会话
- 前端按 `updated_at` 倒序渲染会话列表

### `GET /api/v1/sessions/{id}`
状态：`implemented`

用途：
- 读取单个会话的消息流、上传附件和样例挂接状态

关键响应字段：
```json
{
  "session_id": "string",
  "title": "string",
  "created_at": "string",
  "updated_at": "string",
  "message_count": 3,
  "file_count": 1,
  "attached_private_sample_count": 2,
  "messages": [],
  "files": [],
  "attached_files": [],
  "knowledge_scope_last_used": "mixed",
  "source_summary": {
    "knowledge_scope": "mixed",
    "public_policy_count": 2,
    "private_sample_count": 2,
    "total_citation_count": 4
  }
}
```

当前约束：
- `messages[].role` 当前允许：`user | assistant | system`
- 报告生成成功后，会向当前会话追加一条 `system` 消息

### `PATCH /api/v1/sessions/{id}`
状态：`implemented`

用途：
- 修改会话标题
- 当前主要用于自动标题提升与后续前端手动改名预留

### `POST /api/v1/files`
状态：`implemented / upload-skeleton`

用途：
- 接收文件并绑定到指定 session
- 当前只受控落盘，不参与 retrieval、ask 或 report

请求方式：
- `multipart/form-data`
- 字段：`session_id`、`file`

成功响应草案：
```json
{
  "file_id": "string",
  "session_id": "string",
  "filename": "sample.pdf",
  "size": 1024,
  "mime_type": "application/pdf",
  "stored_at": "2026-04-09T10:35:00+00:00"
}
```

### `GET /api/v1/private-samples`
状态：`implemented`

用途：
- 列出可挂接到当前 session 的 private sample 目录项

### `PUT /api/v1/sessions/{id}/attached-files/private-samples`
状态：`implemented`

用途：
- 用整组替换语义更新当前 session 已挂接的 private sample 集合

请求体：
```json
{
  "doc_ids": ["enterprise_doc_001", "energy_bill_sample_001"]
}
```

## 业务接口

### `POST /api/v1/sessions/{id}/ask`
状态：`implemented`

鉴权：暂定否

内部驱动：当前由 `ai_runtime` 的 `ask` mode 驱动

请求体：
```json
{
  "question": "string",
  "knowledge_scope": "public | private_sample | mixed",
  "top_k": 5,
  "attached_file_ids": []
}
```

响应体：
```json
{
  "answer": "string",
  "mode": "ask",
  "status": "ok | provider_error | invalid_input",
  "citations": [
    {
      "doc_id": "string",
      "title": "string",
      "source_type": "public_policy | private_sample",
      "source": "string",
      "source_url": "string | null",
      "snippet": "string",
      "chunk_id": "string"
    }
  ],
  "source_summary": {
    "knowledge_scope": "public | private_sample | mixed",
    "public_policy_count": 0,
    "private_sample_count": 0,
    "total_citation_count": 0
  },
  "trace_id": "string"
}
```

当前实现约束：
- ask 会带最近 4 轮会话历史进入 `context_builder`
- `knowledge_scope=public`：只走 `policy_retrieve`
- `knowledge_scope=private_sample`：只走 `enterprise_retrieve`
- `knowledge_scope=mixed`：只走 `mixed_retrieve`
- `attached_file_ids` 当前只用于过滤“当前 session 已挂接的 private sample”，不读取上传文件内容
- citations 来源于本地公共政策样本与仓库内脱敏企业样例

错误语义：
- 输入错误：`422`
- provider 调用失败：`502`

### `POST /api/v1/calc-carbon`
状态：`implemented`

鉴权：暂定否

内部驱动：当前直连 `CarbonService`，不经过 `ai_runtime carbon mode`

请求体：
```json
{
  "session_id": "optional",
  "period_label": "2026-Q1",
  "electricity_kwh": 12000,
  "natural_gas_m3": 800,
  "diesel_l": 120
}
```

响应体：
```json
{
  "status": "ok",
  "trace_id": "string",
  "total_emission_kgco2e": 12345.67,
  "breakdown": [
    {
      "item": "electricity",
      "activity_value": 12000,
      "activity_unit": "kWh",
      "factor_value": 0.57,
      "factor_unit": "kgCO2e/kWh",
      "emission_kgco2e": 6840.0,
      "factor_id": "factor-electricity-demo-cn-v0_1_9a"
    }
  ],
  "formula_summary": "排放量 = 活动数据 × 排放因子；总排放量为各分项排放量之和。",
  "citations": [
    {
      "factor_id": "string",
      "source": "string",
      "source_url": "string"
    }
  ]
}
```

错误语义：
- 输入错误：`422`
- session 不存在：`404`
- 因子加载失败或内部计算错误：`500`

### `POST /api/v1/feedback`
状态：`implemented`

鉴权：暂定否

用途：
- 统一接收 ask 与 calc 结果反馈
- 反馈写入运行时数据库

请求体：
```json
{
  "target_type": "ask | calc_carbon",
  "trace_id": "string",
  "session_id": "optional",
  "rating": "up | down",
  "comment": "optional"
}
```

成功响应：
```json
{
  "status": "ok",
  "feedback_id": "string",
  "created_at": "2026-04-09T12:00:00+08:00"
}
```

错误语义：
- 输入错误：`422`
- session 不存在：`404`

### `POST /api/v1/reports`
状态：`implemented`

鉴权：暂定否

内部驱动：当前由 `ReportService` 直接复用 provider factory，不走 `ai_runtime report mode`

请求体：
```json
{
  "session_id": "string",
  "report_type": "policy_summary | mixed_analysis | carbon_summary",
  "title": "可选标题",
  "source_message_ids": [],
  "carbon_result_id": "可选",
  "output_format": "markdown"
}
```

响应体：
```json
{
  "report_id": "string",
  "session_id": "string",
  "report_type": "policy_summary",
  "title": "string",
  "status": "ok",
  "content": "markdown string",
  "output_format": "markdown",
  "citations": [
    {
      "source_type": "public_policy | private_sample | carbon_factor",
      "title": "string",
      "source": "string",
      "source_url": "string | null",
      "snippet": "string",
      "chunk_id": "string | null",
      "factor_id": "string | null"
    }
  ],
  "source_summary": {
    "public_policy_count": 0,
    "private_sample_count": 0,
    "carbon_factor_count": 0,
    "total_citation_count": 0
  },
  "sources": [
    {
      "source_type": "message | citation | carbon_result",
      "source_ref": "string",
      "label": "string",
      "order_index": 0
    }
  ],
  "trace_id": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

模板规则：
- `policy_summary`：至少 1 条 assistant message，且必须带 public policy citations
- `mixed_analysis`：至少 1 条 assistant message，且必须同时带 `public_policy` 和 `private_sample` citations
- `carbon_summary`：必须提供 1 条 `carbon_result_id`

错误语义：
- 输入/来源校验失败：`422`
- session 不存在：`404`
- provider 失败：`502`
- 存储或渲染错误：`500`

### `POST /api/v1/generate-report`
状态：`deprecated alias / implemented`

用途：
- 兼容旧草案口径
- 内部直接转发到 `POST /api/v1/reports`

### `GET /api/v1/reports/{report_id}`
状态：`implemented`

用途：
- 读取单份报告正文、来源快照、引用与 trace 信息

### `PATCH /api/v1/reports/{report_id}`
状态：`implemented`

用途：
- 覆盖当前报告正文和可选标题
- 当前不保留版本 diff

请求体：
```json
{
  "title": "可选",
  "content": "updated markdown"
}
```

### `GET /api/v1/sessions/{id}/reports`
状态：`implemented`

用途：
- 列出当前 session 下的历史报告
- 报告页左侧列表直接消费该接口

成功响应草案：
```json
[
  {
    "report_id": "string",
    "report_type": "policy_summary",
    "title": "string",
    "created_at": "string",
    "updated_at": "string",
    "source_count": 3
  }
]
```

### `GET /api/v1/sessions/{id}/carbon-calculations`
状态：`implemented`

用途：
- 列出当前 session 下可供报告页选择的 calc 结果摘要

成功响应草案：
```json
[
  {
    "trace_id": "string",
    "period_label": "2026-Q1",
    "total_emission_kgco2e": 123.45,
    "created_at": "string"
  }
]
```

## AI Runtime 内部约束
- ask 继续通过 `app.ai_runtime.runtime.orchestrator.run()` 进入运行时
- provider 访问必须经 `app.ai_runtime.providers.factory`
- 当前模式仍冻结为 `ask`、`carbon`、`report`
- `carbon` 与 `report` mode 当前仍保留为统一入口预留位；真实 calc/report 分别先直连 `CarbonService` 与 `ReportService`

## 错误码占位
- `INVALID_INPUT`
- `CONFIG_ERROR`
- `INTERNAL_ERROR`
- `PROVIDER_ERROR`
