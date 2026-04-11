# Chat Streaming Flow

本文件冻结 V1.1.5 的 ask 流式事件流和前后端职责边界。

## 目标

- 让问答默认以 streaming first 方式工作
- 用户消息立即入流
- assistant 先占位，再经历 `pending -> thinking -> streaming -> done/error`
- thinking 与 answer 分流，但 thinking 不落库

## 后端入口

- 保留：`POST /api/v1/sessions/{id}/ask`
- 主入口：`POST /api/v1/sessions/{id}/ask/stream`

## 服务端执行顺序

1. 校验用户身份、session 所有权、scope、问题长度
2. 立即持久化用户消息
3. 立即创建一条 assistant 占位消息
4. 执行 session compaction / context build / grounding
5. 进入 provider 流式消费
6. 持续发出 SSE 事件
7. 流结束时回写同一条 assistant 消息的最终正文、citations、source_summary、trace_id、status
8. 若失败，则回写受控错误文案和错误状态

## SSE 事件契约

### `message_start`

用途：
- 告诉前端本次真实的 `user_message_id`
- 告诉前端本次真实的 `assistant_message_id`
- 返回 `trace_id`

### `status`

允许值：
- `pending`
- `thinking`
- `streaming`
- `done`
- `error`

用途：
- 驱动前端消息状态机

### `thinking_delta`

用途：
- 承接 reasoning / thinking 片段
- 可选显示在折叠 thinking 区

说明：
- thinking 文本只用于运行中 UI，不写入 session 正文

### `answer_delta`

用途：
- 增量输出最终回答正文
- 前端逐 chunk 追加到 assistant 消息内容

### `metadata`

用途：
- 返回最终元数据

至少包含：
- `citations`
- `source_summary`
- `memory_state`

### `done`

用途：
- 流式生命周期完成信号
- 可附带最终状态与元数据补充

### `error`

用途：
- 告诉前端本次生成失败
- 驱动 assistant 消息进入错误态

## 前端状态机

1. 用户点击发送
   - 用户消息立即进入消息流
   - assistant 占位立即进入消息流

2. 收到 `status=pending`
   - 显示“等待开始”

3. 收到 `status=thinking`
   - 显示“思考中”
   - 显示 pulse / heartbeat / three-dots 动态表现

4. 收到 `thinking_delta`
   - 更新 thinking 折叠区内容

5. 收到 `answer_delta`
   - assistant 消息正文逐步增长
   - 生命周期进入 `streaming`

6. 收到 `metadata`
   - 更新 citations、source_summary、memory_state

7. 收到 `done`
   - 生命周期进入 `done`

8. 收到 `error`
   - 生命周期进入 `error`
   - 展示受控错误文案

## 为什么不把 thinking 落库

本轮的目标是改善聊天体感，不是把推理过程当历史正文保存。把 thinking 落库会直接带来两类问题：

- session 历史噪声膨胀
- 用户容易把运行中推理片段误认为最终结论

因此 V1.1.5 明确冻结：

- final assistant content 落库
- citations 落库
- thinking 只做运行时 UI 数据
