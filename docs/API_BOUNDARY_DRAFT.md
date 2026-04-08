# API Boundary Draft
版本：v0.1.8
状态：enterprise-private-sample + mixed scope ask

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
- 验证 API 前缀、配置层和 provider 已接通

成功响应草案：

```json
{
  "app_name": "CarbonRag",
  "version": "v0.1.8",
  "env": "development",
  "api_prefix": "/api/v1",
  "model_provider_mode": "openai_compatible",
  "timestamp": "2026-04-08T12:00:00+08:00"
}
```

## Session 与附件接口

### `POST /api/v1/sessions`

状态：`implemented-minimal`

用途：

- 创建新的对话会话
- 为 ask 多轮对话和附件 / 样例挂接提供主容器

成功响应字段草案：

```json
{
  "session_id": "string",
  "title": "新对话 2026-04-08 18:30",
  "created_at": "2026-04-08T10:30:00+00:00",
  "updated_at": "2026-04-08T10:30:00+00:00",
  "message_count": 0,
  "file_count": 0,
  "attached_private_sample_count": 0
}
```

### `GET /api/v1/sessions`

状态：`implemented-minimal`

用途：

- 列出所有会话
- 前端按 `updated_at` 倒序渲染 session 列表

### `GET /api/v1/sessions/{id}`

状态：`implemented-minimal`

用途：

- 读取单个会话的消息流、上传附件和已挂接样例状态

成功响应字段草案：

```json
{
  "session_id": "string",
  "title": "string",
  "created_at": "string",
  "updated_at": "string",
  "message_count": 2,
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

### `PATCH /api/v1/sessions/{id}`

状态：`implemented-minimal`

用途：

- 修改会话标题
- 当前主要为后端自动标题提升与后续前端手动改名预留

### `POST /api/v1/files`

状态：`implemented-minimal / upload-skeleton`

鉴权：暂定否

用途：

- 接收文件并绑定到指定 session
- 当前只受控落盘，不参与 retrieval 和 ask

请求方式：

- `multipart/form-data`
- 字段：`session_id`、`file`

成功响应字段草案：

```json
{
  "file_id": "string",
  "session_id": "string",
  "filename": "sample.pdf",
  "size": 1024,
  "mime_type": "application/pdf",
  "stored_at": "2026-04-08T10:35:00+00:00"
}
```

当前实现约束：

- 当前只允许保守文档类附件
- 当前大小限制为 20 MB
- 当前文件只做 session 绑定与展示，不参与 ask 推理

### `GET /api/v1/private-samples`

状态：`implemented-minimal`

用途：

- 列出可挂接到当前 session 的 private sample 目录项
- 当前只返回仓库内脱敏样例，不返回真实企业数据

### `PUT /api/v1/sessions/{id}/attached-files/private-samples`

状态：`implemented-minimal`

用途：

- 用整组替换语义更新当前 session 已挂接的 private sample 集合

请求字段草案：

```json
{
  "doc_ids": ["enterprise_doc_001", "energy_bill_sample_001"]
}
```

## 业务接口草案与当前状态

### `POST /api/v1/sessions/{id}/ask`

状态：`controlled-linked / implemented-minimal`

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
  "top_k": 5,
  "attached_file_ids": []
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

- ask 固定从 `POST /api/v1/sessions/{id}/ask` 进入，不再主推旧的无 session 路由
- ask 会带最近 4 轮会话历史进入 `context_builder`
- `knowledge_scope=public`：只走 `policy_retrieve`
- `knowledge_scope=private_sample`：只走 `enterprise_retrieve`
- `knowledge_scope=mixed`：只走 `mixed_retrieve`
- `attached_file_ids` 当前只用于过滤“当前 session 已挂接的 private sample”，不会读取上传文件内容
- 当前 citations 来源于本地公共政策样本与仓库内脱敏企业样例
- 当前不是完整 RAG 平台，也不是完整企业平台，只是第一条 public/private grounding 链路
- 当检索为空时，系统会返回受限回答，`citations` 允许为空

错误语义：

- 输入错误：`422`
- provider 调用失败：`502`

### `POST /api/v1/calc-carbon`

状态：`stub-ready / not implemented`

鉴权：暂定否

内部驱动：未来由 `ai_runtime` 的 `carbon` mode 驱动

### `POST /api/v1/generate-report`

状态：`stub-ready / not implemented`

鉴权：暂定否

内部驱动：未来由 `ai_runtime` 的 `report` mode 驱动

## AI Runtime 内部约束

- ask / calc-carbon / generate-report 都只通过 `app.ai_runtime.runtime.orchestrator.run()` 进入 AI Runtime
- provider 访问必须经 `app.ai_runtime.providers.factory`
- 当前模式只冻结为 `ask`、`carbon`、`report`
- ask 当前允许的检索工具为：`policy_retrieve`、`enterprise_retrieve`、`mixed_retrieve`
- 当前不做多工具自动规划、不做插件系统、不做长期 memory

## 错误码占位

- `NOT_IMPLEMENTED`
- `INVALID_INPUT`
- `CONFIG_ERROR`
- `INTERNAL_ERROR`
