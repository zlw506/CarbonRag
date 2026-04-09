# Private Knowledge Task Flow

## Scope
V1.1.0 把私有知识从“手动挂接样例”推进到“知识条目 + 任务流 + 索引”的最小闭环。

当前覆盖两类来源：
- 用户上传文件
- `data/private_sample/` 中的管理员共享样例

## Core Resources
- `knowledge_items`
- `knowledge_chunks`
- `knowledge_tasks`

## Item Model
每个知识条目至少记录：
- `knowledge_item_id`
- `owner_user_id | null`
- `library_scope = personal | shared`
- `source_type = uploaded_file | private_sample_repo`
- `storage_path`
- `parse_status`
- `ingest_status`
- `index_status`
- `is_enabled`
- `session_attachable`
- `source_hash`
- `source_mtime`
- `last_error`

## Task Model
任务类型：
- `upload_ingest`
- `rebuild`
- `rescan`
- `retry`

任务状态：
- `queued`
- `running`
- `succeeded`
- `failed`

## Upload Flow
1. 用户上传文件。
2. 后端保留 `files` 记录和 session 绑定。
3. 系统创建个人 `knowledge_item`。
4. 系统写入 `upload_ingest` 任务。
5. 任务 runner 解析正文、切块、写入 `knowledge_chunks`。
6. 条目状态推进到 `parsed / ingested / indexed`。
7. 当前 session 可将该条目挂接到 ask / mixed 检索范围。

## Shared Sample Flow
1. 启动或扫描时读取 `data/private_sample/` manifest。
2. 共享样例导入为 `library_scope=shared` 的知识条目。
3. 若文件指纹变化，则条目标记为待更新并进入 `rebuild`。
4. 管理员可在后台触发扫描、重建和失败重试。

## Retrieval Rule
- `public` 仍走公共政策检索。
- `private_sample / mixed` 改为读取已索引的 `knowledge_chunks`。
- 只检索“当前 session 已挂接”的知识条目。
- 私有 citation 区分：
  - `private_sample`
  - `private_upload`

## Failure Handling
- 可提取文本的 `txt / md / csv / xls / xlsx / docx / 可读 pdf` 进入正常解析。
- 无法提取正文的扫描件或旧格式文件进入 `parse_failed`。
- 管理后台和用户侧都能看到失败状态与错误摘要，并触发 `retry`。
