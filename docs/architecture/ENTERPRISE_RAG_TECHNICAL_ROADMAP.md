# CarbonRag 企业级 RAG 技术路线图

版本：V1.3 路线草案

## 定位

本文件沉淀 `deep-research-report.md` 中关于企业级 RAG / GraphRAG / 平台治理的长期方向，用于指导后续 OpenSpec change 拆分。

它不是当前系统行为规格，也不是一次性实现清单。当前系统事实源仍是：

- `openspec/specs/**`
- 当前 active change：`openspec/changes/adopt-lightrag-rag-architecture/**`
- 已合入的架构文档和代码

## 路线原则

- 不整仓 fork `LightRAG`、`RAGFlow`、`Dify`、`FastGPT` 或 `MaxKB`。
- 产品体验可以参考成熟平台，但核心 RAG、权限、任务、检索链路保持 CarbonRag-native。
- 优先实现稳定契约和 disabled-safe adapter，再接入重依赖。
- 每个阶段都必须有 OpenSpec change、可验证功能、回滚方式和测试。
- GPL 或附加许可证风险较高的项目只作为产品/交互参考，不复制核心代码。

## 当前基线

V1.3 已经建立以下最小能力：

- RAG engine service boundary
- `naive` / `mix` retrieval 参数
- structured chunks / references / metadata
- BM25 fallback
- retrieval-only API
- RAG Lab 前端验证入口
- parser / vector / graph / workflow 的初始契约和 disabled-safe 骨架

## 阶段路线

### 阶段 0：RAG Lab 作为统一验证入口

目标：所有新检索能力都先能在 RAG Lab 中看见。

关键能力：

- 显示 API endpoint、strategy、retrieval path、trace id、latency
- 显示 vector / graph / rerank / fallback 状态
- 显示 0 命中提示和请求错误细节
- 支持公共、知识条目、混合范围检索

参考：LightRAG WebUI 的 retrieval testing 思路。

### 阶段 1：统一 RAG 数据契约

目标：解析、切块、索引、检索、引用都走同一组对象。

核心对象：

- `ParsedDocument`
- `DocumentBlock`
- `ChunkRecord`
- `EmbeddingRecord`
- `CitationRef`
- `RetrievalTrace`

参考：Haystack document/component 边界、LlamaIndex node/document 抽象。

### 阶段 2：ParserProvider 文档解析层

目标：先做 provider 边界，再逐步接入更强解析器。

实施顺序：

1. 现有轻量解析器 wrapper。
2. Docling 主解析器试点。
3. MinerU 复杂 PDF fallback。
4. 解析质量评分和 A/B 样本文档回归。

验收重点：

- Markdown/text/table 基本结构可进入 `DocumentBlock`
- 解析失败原因进入知识任务
- 不改变现有上传和知识任务权限边界

参考：Docling、MinerU、RAG-Anything。

### 阶段 3：VectorStoreAdapter 向量索引层

目标：向量库成为可替换 adapter，而不是写死在检索业务里。

接口方向：

- `healthcheck`
- `upsert_chunks`
- `search`
- `delete_by_document`

默认路线：

- 小中型私有化优先 `pgvector`
- 中大规模再评估 Qdrant / Milvus
- Weaviate 作为一体化 RAG 数据库备选

验收重点：

- vector 后端未配置时保持 BM25 fallback
- RAG Lab 可展示 vector backend 状态
- ask/session 默认行为不因实验开关关闭而变化

### 阶段 4：Hybrid Retriever 策略层

目标：检索策略显式化，便于后续组合 BM25、dense、graph、rerank。

策略名：

- `dense_only`
- `bm25_dense_hybrid`
- `citation_first`
- `graph_augmented`

第一版只做 BM25 + vector merge + rerank，不上图谱强依赖。

参考：Haystack retriever pipeline、LightRAG query mode。

### 阶段 5：GraphIndexBuilder 与 LightRAG-style 图谱增强

目标：先定义图谱模型，再接真实图数据库。

核心对象：

- `GraphEntity`
- `GraphRelation`
- `GraphCommunitySummary`
- `GraphCandidate`

实施顺序：

1. runtime DB 模拟图谱记录。
2. RAG Lab 展示 graph candidates。
3. 引入 LightRAG-style local/global/hybrid 策略。
4. Neo4j adapter 评估与接入。

参考：HKUDS/LightRAG、Microsoft GraphRAG、ms-graphrag-neo4j、Neo4j。

### 阶段 6：工作流与任务编排

目标：把索引流程拆成可恢复、可观察的节点。

基础节点：

- `parse_document`
- `chunk_document`
- `upsert_vectors`
- `build_graph`
- `mark_indexed`

短期继续使用当前 task runner；中期再评估 LangGraph / Haystack 的编排思想。

参考：LangGraph 状态机、Haystack pipeline。

### 阶段 7：企业化治理与平台能力

目标：当 RAG 主链路稳定后，再进入企业治理和部署平台化。

方向：

- 身份：Keycloak / OIDC
- 授权：OpenFGA 或 Casbin
- 可观测：OpenTelemetry + traces / metrics / logs
- 发布：Helm / Argo CD / Argo Rollouts
- 安全：Trivy / Cosign / External Secrets / Kyverno 或 OPA

这些不属于 V1.3 直接实现范围。

## 版本节奏建议

| 版本线 | 重点 |
| --- | --- |
| V1.3.x | RAG Lab、统一契约、retrieval-only API、BM25 fallback、adapter 骨架 |
| V1.4.x | ParserProvider、Docling 试点、解析质量评分 |
| V1.5.x | pgvector MVP、向量索引任务、BM25 + vector hybrid |
| V1.6.x | rerank 实用化、检索评测集、RAG Lab 对比模式 |
| V1.7.x | GraphIndexBuilder、实体关系抽取、graph candidates |
| V1.8.x | LightRAG-style local/global/hybrid、Neo4j adapter 评估 |
| V2.x | 企业身份授权、可观测、GitOps、供应链治理 |

## 开工规则

每个阶段正式实现前必须：

1. 创建或扩展 OpenSpec change。
2. 明确影响模块。
3. 明确默认关闭或 fallback 行为。
4. 明确 RAG Lab 验证方式。
5. 跑 `openspec validate --all`、后端测试、前端 typecheck/build。

## 当前不做

- 不直接替换现有 ask/session 流程。
- 不直接引入 Neo4j、Qdrant、Milvus、LangGraph、Haystack 的运行时依赖。
- 不复制 GPL 或附加许可证项目的核心代码。
- 不把企业治理工具提前塞进 V1.3。
