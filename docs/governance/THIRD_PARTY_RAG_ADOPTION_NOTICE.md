# 第三方 RAG 采用说明

V1.6.3 之后，CarbonRag 的 RAG 主线采用“主复现对象 + 算法参考 + 企业蓝图”的方式推进。

## 采用结论

- `RAG-Pro`: #2/tbx2835066135 组内授权可用，作为 V1.6.x 主复现对象。允许直接迁移/改写核心结构与逻辑，但不提交 `3rdparty` 源码。
- `ragPdfSystem`: #2/tbx2835066135 组内授权可用，作为后续企业增强蓝图，重点参考异步处理、对象存储、OCR、评测与 GraphRAG。
- `RMA-MUN/LangChain-RAG-FastAPI-Service`: 许可证未确认，只作为 LangChain、HyDE、Chroma、BM25/vector、rerank 算法参考，不直接复制源码。

## 仓库规则

- `3rdparty/` 保持忽略，不提交源码或 ZIP。
- 迁移到 CarbonRag 的代码必须变成 CarbonRag 原生模块，遵守现有 auth/session/runtime DB 边界。
- 直接迁移的业务结构需在研究文档或代码注释中说明来源。

