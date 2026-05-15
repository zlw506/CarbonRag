# V1.7.3 gov.cn 政策正文抽取审查报告

## 结论

本轮问题不是“没有发现 URL”，而是发现 URL 后没有稳定抽取正文。Scrapy 无结果时会进入 urllib fallback，旧逻辑把 raw HTML 当正文保存，再用通用去标签生成 cleaned/markdown，导致后台预览、质量评分和 RAG 入库都可能看起来成功但实际不可用。

## 逐项定位

1. 试抓超时：前端全局 `httpClient` 使用 30000ms timeout，crawler dry-run/run/publish-to-RAG 被普通请求超时硬杀；V1.7.3 改为 crawler 专用 120000ms。
2. Scrapy no documents：当本地 Scrapy runner 超时或返回空文档时，`PolicyIngestion` 会设置 `scrapy_returned_no_documents` 或 `scrapy_timeout` 并进入 urllib fallback。
3. urllib fallback：旧 fallback 会抓取 raw HTML 并创建 `CrawledDocument(content=raw_html, content_type=text/html)`，未执行 gov.cn 文章正文级抽取。
4. raw HTML：raw 文件可能存在且大小正常，但它只是完整网页，包含导航、页脚、搜索、打印、分享等噪声。
5. cleaned.txt：旧逻辑是通用 HTML 去标签，大小不代表有效正文；V1.7.3 开始强制写正文纯文本并校验长度。
6. document.md：旧逻辑按 raw HTML 去标签结果生成 markdown；V1.7.3 使用 gov.cn extractor 的标题、文号、日期、来源和正文生成。
7. FilePreviewDrawer 为空：旧预览只读 metadata 路径，路径存在但文件为空或内容无效时没有诊断；V1.7.3 增加 artifacts endpoint 和 extraction.json。
8. quality=100 误导：旧 `candidate_quality_score` 混合了官方域名、关键词和 markdown 可用性；V1.7.3 拆成 `extraction_quality_score` 与 `topic_relevance_score`。
9. duplicate 展示误导：`duplicate_content_hash` 仍可能显示为普通待发布；V1.7.3 前端显示“重复内容”，按钮按是否已有 RAG 文档切换。
10. RAG 入库门禁不足：旧 bridge 只按 markdown/cleaned/raw 路径优先创建文档；V1.7.3 发布前检查 markdown/cleaned 大小、预计 chunk 数和抽取质量，quick pipeline 后检查 chunk/index/search smoke。

## 固定验收 URL

- URL: `https://www.gov.cn/zhengce/content/202604/content_7066483.htm`
- 预期标题：`国务院关于推进服务业扩能提质的意见`
- 预期文号：`国发〔2026〕7号`
- 预期发布日期：`2026年04月21日`
- 预期正文片段：`为推进服务业扩能提质，促进服务业优质高效发展`

## V1.7.3 修复证据

- 新增 `backend/app/knowledge/extractors/gov_cn_policy.py`。
- crawler artifact 目录固定包含 `raw.html`、`cleaned.txt`、`document.md`、`extraction.json`。
- 新增 `GET /api/v1/admin/policy-crawler/candidates/{candidate_id}/artifacts`。
- `publish-to-rag` 对空正文、零 chunk、零 indexed chunk、search smoke failed 均拒绝标记 published。
