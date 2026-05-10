# CarbonRag 与 RMA-MUN 差距审计

V1.6.1 已将 LangChain、Chroma、HyDE、BM25、rerank 的模块外形接入 CarbonRag，但它仍不是完整 RMA-MUN 移植。

## 已有进展

- `backend/app/langchain_rag/` 已存在。
- `/api/v1/rag/search`、`/answer`、`/health` 已存在。
- `.env.example` 默认打开 RAG。

## 关键差距

- 新旧 RAG 仍并存，且新 RAG 曾静默 fallback 到旧 RAG。
- `CarbonRagEmbeddings` 曾允许 hash embedding 伪向量，容易掩盖真实向量不可用。
- Ask 主链路仍需统一到 `backend/app/rag` 主脊柱。
- 缺少 RAG-Pro 式知识库、文档状态、chunk 预览、test QA 工作台。

## 处理原则

RMA-MUN 的算法能力保留为 adapter，产品主脊柱切到 RAG-Pro。

