# API Boundary Draft
版本：v0.1.6
状态：ask controlled-linked / public-policy-grounded

## 已开放的最小接口

### `GET /healthz`

用途：

- 提供最小健康检查
- 验证 FastAPI 服务已正常启动

成功响应草案：

```json
{
  "status": "ok"
}
```

### `GET /api/v1/system/info`

用途：

- 提供前端可读取的最小系统信息
- 验证 API 前缀、配置层和 provider stub 已接通

成功响应草案：

```json
{
  "app_name": "CarbonRag",
  "version": "v0.1.6",
  "env": "development",
  "api_prefix": "/api/v1",
  "model_provider_mode": "openai_compatible",
  "timestamp": "2026-04-03T13:00:00+00:00"
}
```

## 业务接口草案与当前状态

### `POST /api/v1/ask`

状态：`controlled-linked / public-policy-grounded`

鉴权：暂定否

内部驱动：当前已由 `ai_runtime` 的 `ask` mode 驱动

内部最小 schema 映射：

- 输入落到 `ChatRequest`
- 输出落到 `ChatResponse` / `RuntimeResult`

请求字段草案：

```json
{
  "question": "string",
  "knowledge_scope": "public | private_sample | mixed",
  "top_k": 5
}
```

成功响应字段草案：

```json
{
  "answer": "string",
  "mode": "ask",
  "status": "ok | provider_error | invalid_input",
  "citations": [
    {
      "doc_id": "string",
      "title": "string",
      "source": "string",
      "source_url": "string",
      "snippet": "string",
      "chunk_id": "string"
    }
  ],
  "trace_id": "string"
}
```

当前实现约束：

- 当前只支持单轮问答
- 当前 ask 只支持 `knowledge_scope=public`
- `mixed` 与 `private_sample` 当前都返回 `422`
- 当前 citations 来源于本地公共政策样本语料
- 当前 ask 已固定先走 `policy_retrieve`，再进入 provider 回答
- 当前不是完整 RAG 平台，只是第一条 public-policy grounding 链路
- 当检索为空时，系统会返回受限回答，`citations` 允许为空

### `POST /api/v1/calc-carbon`

状态：`stub-ready / not implemented`

鉴权：暂定否

内部驱动：未来由 `ai_runtime` 的 `carbon` mode 驱动

内部最小 schema 映射：

- 输入落到 `ChatRequest`
- 输出落到 `RuntimeResult`

请求字段草案：

```json
{
  "scenario": "demo_basic",
  "activity_data": {
    "electricity_kwh": 0,
    "fuel_liters": 0
  }
}
```

成功响应字段草案：

```json
{
  "mode": "carbon",
  "status": "stub_ready",
  "scenario": "demo_basic",
  "total_emission": 0,
  "unit": "kgCO2e",
  "breakdown": [],
  "trace_id": "string"
}
```

### `POST /api/v1/generate-report`

状态：`stub-ready / not implemented`

鉴权：暂定否

内部驱动：未来由 `ai_runtime` 的 `report` mode 驱动

内部最小 schema 映射：

- 输入落到 `ChatRequest`
- 输出落到 `RuntimeResult`

请求字段草案：

```json
{
  "report_type": "demo_summary",
  "source_refs": [],
  "carbon_result_ref": "string"
}
```

成功响应字段草案：

```json
{
  "mode": "report",
  "status": "stub_ready",
  "report_type": "demo_summary",
  "format": "markdown",
  "content": "string",
  "trace_id": "string"
}
```

## AI Runtime 内部约束

- 未来 ask / calc-carbon / generate-report 都只通过 `app.ai_runtime.runtime.orchestrator.run()` 进入 AI Runtime
- provider 访问必须经 `app.ai_runtime.providers.factory`
- 当前模式只冻结为 `ask`、`carbon`、`report`
- 当前 ask 已固定接入 `policy_retrieve`
- 其他工具仍保持双碳业务 stub：`enterprise_retrieve`、`carbon_factor_lookup`、`carbon_calc`、`report_draft`

## 错误码占位

- `NOT_IMPLEMENTED`
- `INVALID_INPUT`
- `CONFIG_ERROR`
- `INTERNAL_ERROR`
