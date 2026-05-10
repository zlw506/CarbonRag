# RAG-Pro Port Map

## 迁移目标

RAG-Pro 的知识库系统映射到 CarbonRag：

| RAG-Pro 概念 | CarbonRag 落点 |
|---|---|
| KnowledgeBase | `rag_knowledge_bases` + `backend/app/rag/kb` |
| Document | `rag_documents` + existing `knowledge_items/files` bridge |
| Chunk | `rag_chunks` + existing `knowledge_chunks` bridge |
| parse/chunk/index status | `backend/app/rag/documents/status.py` |
| Milvus Lite/Milvus | `backend/app/rag/vector/milvus_store.py` adapter |
| in-memory/local fallback | `backend/app/rag/vector/memory_store.py` degraded adapter |
| hybrid retrieval | `backend/app/rag/retrieval/hybrid_rrf.py` |
| rerank | `backend/app/rag/retrieval/rerank.py` |
| test QA | `backend/app/rag/qa/test_qa.py` + `/api/v1/rag/test-qa` |

## 本轮落地边界

本轮先落产品骨架、RRF trace、内存/Chroma/Milvus adapter 接口和测试问答。真实 BGE-M3/Milvus Lite 安装验证作为后续增强，但 API 和 trace 不再伪装成功。

