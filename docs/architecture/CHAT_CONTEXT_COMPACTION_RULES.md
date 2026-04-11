# Chat Context Compaction Rules

本文件冻结 V1.1.5 的聊天上下文拼装与裁剪规则。目标不是重新设计 memory 体系，而是把已有的 summary / recent window / grounding 规则明确下来。

## 核心原则

1. 当前问题永远保留
2. `session_summary` 优先级高于旧原始消息
3. 最近窗口优先于更早窗口
4. grounding 结果必须进入，但数量受预算控制
5. `memory_notes` 只做预留读路径，预算紧张时优先裁剪

## Ask 上下文拼装顺序

V1.1.5 固定顺序如下：

1. `session_summary`
2. 最近 6 轮高优先消息
3. grounding 结果
4. 当前问题

说明：
- `session_summary` 负责承接更早历史
- 最近窗口负责保留短期对话连续性
- grounding 负责本轮事实依据
- 当前问题始终是最后输入点

## 自动压缩触发

ask 进入运行时前，系统会估算：

- `session_summary`
- 未压缩最近消息
- grounding 结果
- 当前问题

当估算占用超过预算阈值，或未压缩消息量超过阈值时：

- 把最近窗口之外的更早 `user/assistant` 消息压入 `session_summary`
- 保留最近 6 轮完整消息

## 裁剪优先级

当上下文仍然接近预算上限时，按下面顺序裁剪：

1. 先裁 `memory_notes`
2. 再减少 grounding 条数
3. 最后从最近窗口中最旧的轮次开始裁

明确不裁：

- 当前问题
- `session_summary`

## 前端可感知提示

V1.1.5 不新增 memory 页面，但必须让用户知道 compaction 已生效。因此 Ask 页默认显示轻量上下文胶囊，至少包含：

- 当前上下文占用（估算）
- 是否已压缩
- 当前回答使用了“最近 N 轮 + 会话摘要 + M 条依据”

展开后再显示：

- 摘要更新时间
- 已摘要覆盖消息数
- 更完整的 context source 说明

## Boundary

本文件只描述聊天上下文，不描述知识库检索和长期记忆写入。

- `knowledge library`：用户主动上传或入库的知识条目
- `memory`：对话过程中的上下文组织能力

两者不能混用，也不能把检索片段回写为 session summary。
