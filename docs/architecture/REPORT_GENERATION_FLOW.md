# Report Generation Flow

版本：`v0.2.0`

## 目标
把 CarbonRag 从“会问、会算”推进到“会产出结构化结果文档”。

当前报告链路遵循三个原则：
- 报告必须绑定某个 `session`
- 报告必须显式记录来源
- 报告正文采用“模板驱动 + 受控 LLM”，不是自由发挥长文

## 当前支持的报告类型

### `policy_summary`
适用场景：
- 基于 ask 已得到的公共政策依据
- 生成政策解读摘要

最小来源要求：
- 至少 1 条 assistant message
- 所选消息中必须包含 `public_policy` citations

### `mixed_analysis`
适用场景：
- 同时参考公共政策依据和脱敏企业样例
- 输出“政策要求 + 样例现状 + 初步建议”的结构化分析

最小来源要求：
- 至少 1 条 assistant message
- 所选消息中必须同时包含 `public_policy` 与 `private_sample` citations

### `carbon_summary`
适用场景：
- 基于一条已经落库的 calc-carbon 结果
- 输出核算周期、活动数据、公式与因子说明

最小来源要求：
- 必须提供 `carbon_result_id`

## 核心链路

### 1. 前端进入报告页
报告页按当前 `session` 工作，不允许生成漂在会话之外的独立报告。

页面会加载：
- 当前 session 详情
- 当前 session 下的报告列表
- 当前 session 下可选 carbon calculation 列表

### 2. 选择来源
前端会根据报告类型默认选择来源：
- `policy_summary`：最近一条带 public citations 的 assistant 消息
- `mixed_analysis`：最近一条同时带 public/private citations 的 assistant 消息
- `carbon_summary`：最近一条 carbon calculation 结果

用户也可以手动调整：
- `source_message_ids`
- `carbon_result_id`
- 标题

### 3. 调用生成接口
主入口：

```text
POST /api/v1/reports
```

兼容入口：

```text
POST /api/v1/generate-report
```

## 后端内部流

### `ReportService`
`ReportService` 是本轮报告链路的统一服务层，负责：
- 校验 session 是否存在
- 校验 assistant message / carbon result 是否属于当前 session
- 检查报告类型与来源组合是否合法
- 调用 provider 生成章节内容
- 持久化报告与来源
- 回写一条 `system` 消息到当前 session

### `composer`
`composer` 负责把来源拼成生成上下文：
- selected assistant messages
- dedup 后的 ask citations
- 可选 carbon result
- source summary
- 模板名称和章节列表

### `templates`
模板在 `templates.py` 中集中定义，当前固定 3 类：
- 政策解读摘要
- 政策 + 企业样例分析
- 碳核算结果说明

模板约束的是：
- 标题
- 章节顺序
- 允许的来源组合

### `renderer`
`renderer` 当前只负责把结构化章节渲染成 Markdown。

provider 需要返回：
- `title`
- `sections[]`

每个 section 至少包含：
- `heading`
- `body`

最终输出会自动追加“依据列表”章节。

## 来源记录

每份报告都会写入两层来源信息：

### `reports`
保存报告正文与快照：
- `content`
- `citations_json`
- `source_summary_json`
- `trace_id`

### `report_sources`
保存显式来源：
- `message`
- `citation`
- `carbon_result`

这样做的目的：
- 报告重开时不必再次推导
- 前端右侧依据面板可直接复现来源
- session 维度可以回看历史报告

## 与 session 的关系
报告不是漂浮资源，必须属于某个 `session`。

报告生成成功后，后端会在当前会话追加一条 `system` 消息，例如：
- 已生成报告标题
- 报告类型
- `report_id`

这样 session 继续保持“总工作台”角色，而不是 ask 和 report 各走一套。

## 与 calc-carbon 的关系
`carbon_summary` 模板直接消费已落库的 calc 结果，而不是重新计算。

当前衔接规则：
- 通过 `GET /api/v1/sessions/{id}/carbon-calculations` 获取可选结果
- 通过 `carbon_result_id` 绑定一条记录
- 自动把 factor citations 带入 report citations

## 与双环境的关系
- `local-dev`：SQLite fallback，报告用于本地实验和模板调试
- `cloud-stable`：PostgreSQL，报告用于稳定展示和外部测试

两边报告数据不共享，这属于设计预期。

## 当前明确不做
- docx / pdf 导出
- 富文本编辑器
- 报告版本 diff
- 跨会话报告聚合
- 附件自动解析进报告
- 长期 memory 驱动报告个性化
