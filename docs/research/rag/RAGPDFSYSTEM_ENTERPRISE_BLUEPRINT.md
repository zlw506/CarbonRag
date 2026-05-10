# ragPdfSystem 企业增强蓝图

ragPdfSystem 暂不作为 V1.6.3 主复现对象。它的价值在后续企业增强：

- Celery/RabbitMQ: 大文件解析、索引、OCR 的异步任务队列。
- MinIO: 原始文件和解析结果对象存储。
- Milvus: 生产级向量库。
- OCR/结构分析: 扫描 PDF、表格、图片理解。
- RAGAS-like 评测: 自动生成 QA、命中率、忠实度与报告。
- GraphRAG: 文档、实体、政策、碳因子的关系图谱。

V1.6.3 只建立 `knowledge_graph_nodes`、`knowledge_graph_edges` 数据底座，不复制 ragPdfSystem 企业基础设施。

