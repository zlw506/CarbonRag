# Change: rag-pro-real-vector-ask-e2e

## Why

V1.6.3 已经搭出 RAG-Pro 式知识库主脊柱，但 Milvus Lite/BGE-M3 仍未真实闭环，AskPage 也还没有把 `kb_id` 与检索模式带入真实聊天主链路。本轮要把结构基线推进到可验收的真实向量、真实知识库选择和真实文档端到端问答。

## What Changes

- 默认 RAG 向量后端切到 `milvus_lite`，接入 BGE-M3 dense+sparse embedding 和 BGE reranker。
- 文档 index 阶段真实写入 Milvus Lite/Milvus；模型或向量库不可用时显式失败/降级，不允许 hash/fake vector 伪成功。
- Ask 请求增加 `kb_id`、`rag_mode`，AskPage 可选择知识库与检索模式。
- KnowledgeBaseWorkbench 展示 vector backend、index warning、test QA trace。
- 增加真实向量 smoke 脚本和测试，CI 可 mock，#1 本地验收必须跑真实 Milvus Lite/BGE-M3。

## Out Of Scope

- 不新增第三套 RAG facade。
- 不接入 ragPdfSystem 的 Celery/RabbitMQ/MinIO。
- 不做知识图谱 UI。
