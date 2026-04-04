# Public Policy Retrieval Flow

版本：v0.1.6

## 目标

本轮只为 ask mode 建立第一条带公共政策依据的 grounding 链路，不追求完整 RAG 平台，不接入企业私有数据，也不引入自动爬虫与向量数据库。

## 公共语料结构

当前语料位于 `data/public/corpus/`：

```text
data/public/corpus/
├─ docs/
│  ├─ policy_001.md
│  ├─ policy_002.md
│  ├─ policy_003.md
│  ├─ policy_004.md
│  └─ policy_005.md
└─ manifest.json
```

每份文档使用 frontmatter 固定以下元信息：

- `doc_id`
- `title`
- `source`
- `source_url`
- `issued_at`
- `region`
- `doc_type`

正文不是 PDF 原文，而是基于官方公开来源整理的标准化摘录，用于支撑首条可控问答演示。

## 文档加载方式

`app.retrieval.public_corpus_loader` 负责：

- 读取 `manifest.json`
- 解析每个 Markdown 文件的 frontmatter
- 校验 manifest 与 frontmatter 的元信息一致
- 输出统一的 `PublicPolicyDocument`

这样做的目的是让 citations 永远能回溯到固定 `doc_id` 与来源链接，而不是让模型自行编造引用。

## 切分方式

`app.retrieval.public_chunker` 当前采用轻量、稳定、可解释的规则：

- 先按空行分段
- 去掉空段并清洗多余空白
- 超长段落按句号、问号、分号等边界继续切开
- 目标最小 chunk 长度约 80 字
- 单 chunk 上限约 420 字
- 生成稳定 `chunk_id`，格式如 `policy_001_chunk_01`

本轮强调稳定和可解释，不追求复杂语义切分。

## 检索方式

`app.retrieval.public_retriever` 当前使用：

- `jieba.lcut_for_search` 分词
- `rank-bm25` 本地 BM25 排序
- 标题命中轻微 boost
- `top_k` 截断返回

这套方案的优点是部署轻、结果可解释、无需额外向量库服务，适合 v0.1.6 的首轮 grounding 演示。

## Ask Mode 接入方式

ask mode 在 v0.1.6 被固定为单工具受控模式：

1. `POST /api/v1/ask` 接收请求
2. 路由层只允许 `knowledge_scope=public`
3. `orchestrator.run()` 固定先调用 `policy_retrieve`
4. retriever 返回政策片段和 citation 元信息
5. `context_builder` 把政策片段注入 provider 的 system prompt
6. provider 基于片段生成 answer
7. `response_formatter` 从 retrieval result 直接生成 citations

本轮不允许模型自己决定是否检索，也不允许多工具自动规划。

## Citations 生成方式

`citations` 不由模型生成，而是直接来自 retriever 命中的 chunk：

```json
{
  "doc_id": "policy_001",
  "title": "国务院关于印发2030年前碳达峰行动方案的通知",
  "source": "国务院",
  "source_url": "https://www.gov.cn/...",
  "snippet": "命中的政策片段",
  "chunk_id": "policy_001_chunk_01"
}
```

因此 citations 的可信边界是明确的：

- 当前只代表“命中了本地公共政策样本”
- 不代表“已覆盖全国全部政策”
- 不代表“已完成完整知识库与引用回溯系统”

## 当前不做

- 企业私有数据接入
- 完整向量数据库平台
- 自动抓取与自动更新
- 多轮记忆
- 多工具调度
- 模型生成 citation
