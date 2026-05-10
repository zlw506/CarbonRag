# 四项目 RAG 纵向审查

| 维度 | CarbonRag 当前 | RMA-MUN | RAG-Pro | ragPdfSystem |
|---|---|---|---|---|
| 完整度 | 中：产品壳强，RAG 主脊柱弱 | 中高：算法链完整 | 高：知识库产品链完整 | 高：企业架构完整 |
| 企业性 | 中：已有用户/报告/治理 | 中 | 中高 | 高 |
| RAG 核心技术 | BM25/Chroma/rerank 外形已有 | HyDE + Chroma + BM25/vector + rerank | Milvus Lite/Milvus + BGE-M3 + RRF + rerank | hybrid + rerank + 多跳 |
| 文档解析 | V1.5.1 Docling-first | 多格式上传 | 常见文档上传 | OCR/结构/表格强 |
| 知识库工作台 | 弱 | 弱 | 强 | 中高 |
| 检索质量 | 待验证 | 强 | 强 | 强 |
| rerank | 有但需验证 | CrossEncoder | bge-reranker | reranker |
| 评测体系 | 弱 | LangSmith | Test QA | RAGAS-like |
| 部署复杂度 | 中 | 中 | 低到中 | 高 |
| 融合难度 | 本项目 | 中 | 最低 | 高 |
| 短期落地 | 需要重构 | 算法参考 | 最适合 | 不适合全量接入 |
| 长期扩展 | 高 | 中 | 高 | 高 |
| 知识图谱潜力 | 有底座 | 非重点 | 目录空壳 | GraphRAG 蓝图 |

## 决策

V1.6.3 后续主复现对象固定为 `RAG-Pro`。`RMA-MUN` 只保留为算法与 LangChain 参考，`ragPdfSystem` 保留为企业化异步处理、评测、对象存储和 GraphRAG 蓝图。

