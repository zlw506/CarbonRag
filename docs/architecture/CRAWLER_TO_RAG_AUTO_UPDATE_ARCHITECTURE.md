# Crawler to RAG Auto Update Architecture

V1.7.0 固定目标是把现有官方政策 crawler 接到 RAG-Pro KB quick pipeline，而不是新增一个大而全爬虫平台。

## 正式链路

```text
official source registry
-> crawl run
-> raw artifact / staging
-> cleaned text + markdown artifact
-> candidate review
-> publish-to-rag
-> shared RAG KB: 官方政策自动更新库
-> quick pipeline: parse -> chunk -> index -> search smoke
-> /rag/search and AskPage citations
```

## 技术边界

- `Scrapy/Scrapyd`：当前执行器。`local_scrapy` 用于本地 smoke，`scrapyd` 是后续稳定运行推荐路线。
- `Crawl4AI`：本轮学习 LLM-ready markdown、缓存、动态页面和链接抽取思想，不作为运行时依赖。
- `Crawlab`：本轮学习 source/run/task/log/result/schedule/worker 治理模型，不引入 MongoDB、SeaweedFS、master/worker 平台。
- `RAG-Pro KB`：crawler 发布后的唯一正式入库目标。
- 旧 knowledge publish：保留兼容，但不是 V1.7.0 验收路径。

## 安全默认值

```env
RAG_ENABLE_POLICY_CRAWLER=true
RAG_POLICY_CRAWLER_BACKEND=local_scrapy
RAG_POLICY_LIVE_CRAWLER_MANUAL_ENABLED=true
RAG_POLICY_LIVE_CRAWLER_SCHEDULED_ENABLED=false
RAG_POLICY_LIVE_CRAWLER_AUTO_PUBLISH=false
```

默认不自动定时、不自动发布。管理员必须手动运行 source，并在候选列表中显式点击“发布到 RAG”。

## Candidate Artifact Metadata

每个 candidate 至少通过 metadata 记录：

- `canonical_url`, `http_status`, `fetched_at`
- `raw_storage_path`, `cleaned_storage_path`, `markdown_storage_path`
- `content_hash`, `previous_content_hash`, `change_type`, `skip_reason`
- `crawler_backend`, `robots_obey`, `duration_ms`
- `error_stage`, `error_detail`
- `rag_kb_id`, `rag_doc_id`, `rag_pipeline_status`, `rag_indexed_chunk_count`

失败阶段统一使用 `fetch/discover_links/parse_html/download_binary/clean_markdown/topic_filter/dedupe/stage/publish_to_rag/rag_quick_pipeline`。

## 验收

最小真实验收是：`gov-cn-policy-library` 手动运行后产生至少一个 candidate，管理员发布到 RAG，quick pipeline 完成，`/rag/search` 对“碳达峰”命中该 KB 文档，AskPage 选择该 KB 后可以引用。
