# Crawl4AI / Crawlab Adoption Notes

本轮只学习两个本地参考项目：

- `3rdparty/crawl4ai-main/crawl4ai-main`
- `3rdparty/crawlab-main/crawlab-main`

不下载 Firecrawl；不引入 Firecrawl 的 AGPL 许可证和 Web data API 部署复杂度。

## Crawl4AI 可迁移思想

- 网页输出以 clean markdown/text 为主，而不是只保存原 HTML。
- 保留 raw artifact、cleaned artifact、markdown artifact，便于追踪清洗质量。
- 用 content hash 和缓存思路减少重复入库。
- 对动态页面、链接抽取、浏览器池的能力先作为后续增强方向，本轮不直接接入运行时。

## Crawlab 可迁移思想

- 用 source/run/task/log/result/schedule/worker 的语言组织 crawler 治理。
- 每次 run 要可追踪文档数、candidate 数、失败阶段和错误详情。
- candidate/result 与发布动作分离，避免抓取成功直接污染正式知识库。
- 本轮不接 MongoDB、SeaweedFS、master/worker 和 spider 部署平台。

## CarbonRag V1.7.0 选择

现阶段 CarbonRag 已有 `policy_live_crawler`、Scrapy/Scrapyd provider、Admin policy-crawler endpoints、RAG-Pro KB pipeline。最高价值不是重写爬虫，而是新增 `publish-to-rag` bridge，让候选政策进入 `官方政策自动更新库` 并执行 quick pipeline。
