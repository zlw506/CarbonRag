# Private Sample Retrieval Flow

## 目标

v0.1.8 的 private sample retrieval 只解决一件事：让当前 session 在受控范围内检索仓库内的脱敏企业样例，并把结果作为 ask 的依据之一。

## 样例语料结构

`data/private_sample/corpus/` 当前拆为两类：

- `docs/`：脱敏背景说明、设备与项目概况等 Markdown 文档
- `tables/`：脱敏的能耗、产量、物流 CSV 样例

所有样例都通过 `manifest.json` 建索引，字段包括：

- `doc_id`
- `title`
- `source_type`
- `sample_type`
- `business_topic`
- `filepath`
- `session_attachable`

## 加载方式

后端通过 `private_corpus_loader.py` 统一读取 `manifest.json`，再按类型加载文件内容：

- Markdown：读取 frontmatter 并校验元信息
- CSV：读取表格后转成“每行一条自然语言描述”的轻量文本

## 切分方式

### Markdown

- 先按空行切段
- 再按标点分割过长段落
- 最终生成稳定的 `chunk_id`

### CSV

- 每一行转成一条结构化文本片段
- 片段形如“样例表《月度能耗台账样例》第 1 行：month=...；electricity_kwh=...”
- `chunk_id` 形如 `energy_bill_sample_001_row_01`

## 检索方式

v0.1.8 仍采用轻量本地检索：

- 分词：`jieba.lcut_for_search`
- 排序：`BM25`
- 输入过滤：只在当前 session 已挂接的 private sample 集合中检索

这意味着：

- 没有挂接样例时，`private_sample` 不会扫描整个仓库
- `attached_file_ids` 当前只作为已挂接样例的二次过滤条件
- 上传文件不会进入 private retrieval

## ask mode 接入

当 `knowledge_scope=private_sample` 时：

1. ask 路由读取当前 session 已挂接的样例
2. orchestrator 选择 `enterprise_retrieve`
3. retriever 返回 private sample 片段
4. context builder 注入样例上下文
5. provider 基于这些样例片段作答

## 引用生成

citations 直接来自 retriever 返回的命中结果，不由模型生成。

每条 citation 至少包含：

- `doc_id`
- `title`
- `source_type=private_sample`
- `source`
- `source_url=null`
- `snippet`
- `chunk_id`

## 当前边界

- 这些样例只是脱敏演示数据
- 当前不是正式企业审计链路
- 当前不做用户上传文件解析
- 当前不做完整知识库平台化
