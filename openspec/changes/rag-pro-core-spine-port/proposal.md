# Change: rag-pro-core-spine-port

## Why

CarbonRag 的 RAG 目前仍存在旧 `backend/app/rag`、过渡 `backend/app/langchain_rag` 与 Ask 主链路之间的割裂。V1.6.3 要把 RAG 从“接口和算法补丁”升级为 RAG-Pro 式知识库产品主脊柱：知识库、文档状态、chunk 管理、hybrid 检索、rerank、test QA 与 Ask 引用闭环。

## What Changes

- 以 `backend/app/rag` 作为唯一 RAG 主入口。
- 将 `backend/app/langchain_rag` 降级为算法适配层，不再作为并行主线。
- 新增 KnowledgeBase、Document、Chunk、状态机、vector adapter、RRF hybrid search、rerank trace、test QA。
- 新增 `/api/v1/kb` 产品化 API 和重构 `/api/v1/rag/*` API。
- 新增 KnowledgeBaseWorkbench 前端入口，AskPage 后续通过新 RAG 主入口选择知识库与检索模式。

## Out Of Scope

- 不接入 ragPdfSystem 的 Celery、RabbitMQ、MinIO 全套。
- 不做大图 UI，只建立知识图谱节点/边数据底座。
- 不提交 `3rdparty` 参考源码。

