# Design: RAG-Pro Core Spine Port

## Direction

V1.6.3 采用 RAG-Pro 的产品脊柱：`KnowledgeBase -> Document -> Chunk -> VectorStore -> HybridRetriever -> Rerank -> Answer/TestQA -> Citation/Trace`。

CarbonRag 保留现有用户、session、AskPage、文件解析、citation 和治理系统。RAG-Pro 的逻辑迁移为 CarbonRag 原生代码，使用 CarbonRag 的权限和 runtime DB。

## Backend Shape

- `backend/app/rag/kb/*`: KB/Document/Chunk 数据模型、存储、服务。
- `backend/app/rag/documents/*`: 文档状态机、分块、从现有 knowledge/file 结果导入。
- `backend/app/rag/vector/*`: Milvus/Chroma/Memory adapter 接口。
- `backend/app/rag/retrieval/*`: dense/sparse/RRF/rerank。
- `backend/app/rag/qa/*`: answer、test QA、trace。
- `backend/app/rag/service.py`: 统一 RAG 主入口，保留旧 `RagEngineService` 兼容但新 API 默认走 `RagSpineService`。

## Degradation Rules

- 真实向量不可用时返回 `degraded=true` 和 `vector unavailable` trace，不允许 hash embedding 伪装成功。
- rerank 不可用时返回 `rerank_applied=false` 与 warning。
- 旧 RAG 只作为显式兼容接口，不作为新 `/rag/search` 的静默 fallback。

