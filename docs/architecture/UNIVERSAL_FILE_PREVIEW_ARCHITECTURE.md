# 通用文件预览架构

V1.7.2 将聊天附件、知识库文档、RAG citation、爬虫候选文件统一到一个“逻辑 ID -> 服务端解析 -> 前端抽屉预览”的入口。

## 目标

- 前端不再直接接触 `storage_path`。
- 只通过 `source_type + source_id` 请求预览。
- 后端按权限解析真实路径，并做目录边界校验。
- 预览优先展示已解析 Markdown / text / chunks；原始文件只用于 PDF、图片、文本等可安全内嵌或下载。

## Source Types

- `session_file`：聊天上传文件，`source_id=file_id`。
- `rag_document`：RAG-Pro 知识库文档，`source_id=doc_id`，必须传 `kb_id`。
- `crawler_candidate`：实时政策爬虫候选文件，`source_id=candidate_id`，仅管理员可读。
- `knowledge_item`：旧知识条目兼容入口，`source_id=knowledge_item_id`。

## API

- `GET /api/v1/file-previews/{source_type}/{source_id}`
- `GET /api/v1/file-previews/{source_type}/{source_id}/raw`

`rag_document` 必须追加 `?kb_id=...`。

## Response

统一返回：

- `title / filename / mime_type / size / status / source_url`
- `markdown`：优先解析结果。
- `text`：优先解析文本，fallback 到 cleaned/raw 文本。
- `chunks`：对应 knowledge chunks 或 RAG chunks。
- `metadata`：解析器、hash、source、candidate/run、错误阶段等。
- `raw_preview_url / raw_download_url`：原始文件预览或下载入口。

## 权限与安全

- 聊天附件只能 owner 或 admin 查看。
- RAG 文档按 KB 可见性和 owner 校验。
- 爬虫候选文件只允许 admin 查看。
- 后端只读取已登记路径，并限制在 `upload_dir`、`public_data_dir`、`backend/data`、`data` 下。
- DOCX/XLSX/PPTX 本轮不做原版在线排版渲染，只展示解析预览、纯文本和 chunks，并提供原文件入口。
