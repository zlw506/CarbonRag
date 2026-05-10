# Tasks

- [x] 重建 GitNexus 索引并确认 RAG/KB/AskPage 影响面。
- [x] 新增 BGE-M3 embedder 和 Milvus Lite/Milvus vector adapter。
- [x] 文档 index 阶段写入真实 vector backend，并在失败时标记 failed/degraded。
- [x] 接入 BGE reranker，失败时显式 `rerank_applied=false`。
- [x] Ask 请求、AI runtime tool、前端 AskPage 增加 `kb_id` / `rag_mode`。
- [x] KnowledgeBaseWorkbench 展示 vector backend 与 index warnings。
- [x] 新增真实向量 smoke 脚本。
- [ ] 完成 OpenSpec、后端测试、前端 typecheck/build。
- [ ] 本地安装真实依赖后执行 Milvus Lite/BGE-M3 smoke。
