# Design: rag-pro-real-vector-ask-e2e

## Backend

`backend/app/rag` 继续作为唯一 RAG 主入口。Milvus Lite adapter 负责 collection 创建、chunk vector 写入和 dense 查询；BGE-M3 embedder 负责 dense+sparse 生成；BGE reranker 负责 query-passage 重排序。任何真实依赖不可用都必须进入 warning/degraded/error trace。

## Ask Flow

AskPage 发送 `kb_id` 和 `rag_mode`。AI runtime 的 `langchain_rag_search` 工具读取这两个字段并调用 `RagSpineService.search()`。响应 metadata 透出 retrieval trace，前端以 tag 形式展示 backend、dense、sparse、RRF、rerank 和 degraded 状态。

## Local Verification

CI 使用 monkeypatch/fake runtime 验证 contract；本地验收用 `scripts/rag-pro-real-vector-smoke.ps1` 触发真实 BGE-M3 + Milvus Lite 路径。
