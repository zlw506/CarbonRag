# API Boundary Draft
版本：v0.0.2
状态：draft only / not implemented

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
  "version": "v0.0.2",
  "env": "development",
  "api_prefix": "/api/v1",
  "model_provider_mode": "cloud_api_stub",
  "timestamp": "2026-04-03T13:00:00+00:00"
}
```

---

## 草案接口

以下接口仅冻结边界，不在 v0.0.2 实现。

### `POST /api/v1/ask`

状态：`draft only / not implemented`

鉴权：暂定否

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
  "citations": [
    {
      "source_id": "string",
      "title": "string",
      "snippet": "string"
    }
  ],
  "trace_id": "string"
}
```

### `POST /api/v1/calc-carbon`

状态：`draft only / not implemented`

鉴权：暂定否

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
  "scenario": "demo_basic",
  "total_emission": 0,
  "unit": "kgCO2e",
  "breakdown": [],
  "trace_id": "string"
}
```

### `POST /api/v1/generate-report`

状态：`draft only / not implemented`

鉴权：暂定否

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
  "report_type": "demo_summary",
  "format": "markdown",
  "content": "string",
  "trace_id": "string"
}
```

## 错误码占位

- `NOT_IMPLEMENTED`
- `INVALID_INPUT`
- `CONFIG_ERROR`
- `INTERNAL_ERROR`
