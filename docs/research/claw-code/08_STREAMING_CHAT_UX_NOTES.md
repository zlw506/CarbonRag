# V1.1.5 Streaming Chat UX Notes

本轮强制参考了 `3rdparty/claw-code-study` 中与 `fix/ui-parity` 对齐的运行时和交互资料，但只收窄到聊天体验本身，不继续扩后台或插件面。

## 本轮借了什么

1. streaming first 的聊天心智
   - 回答不再等整段结束后一次性落地，而是先挂 assistant 占位，再持续增量输出。
   - CarbonRag 对应实现：Ask 页默认优先走 `POST /api/v1/sessions/{id}/ask/stream`。
   - 参考点：`fix_ui_parity_snapshot` 中对 runtime streaming 和事件分发的处理方式。

2. provider abstraction 不直接等于 UI
   - 上游流式事件先在 provider/runtime 层做分类，再由前端决定怎么呈现。
   - CarbonRag 对应实现：SSE 事件冻结为 `message_start / status / thinking_delta / answer_delta / metadata / done / error`，前端只消费这些稳定事件。
   - 参考点：`rust/crates/api/src/sse.rs` 的 frame 解析思路。

3. session state / compaction 必须可感知
   - session summary 和 compaction 不是只存在于后台逻辑里，用户至少要能知道“当前不是每轮都从零开始”。
   - CarbonRag 对应实现：把大块 memory 状态改成上下文胶囊，默认只显示摘要后的上下文来源和占用情况。
   - 参考点：`rust/crates/runtime/src/session.rs` 与 `rust/crates/runtime/src/compact.rs` 的消息角色与压缩窗口处理。

4. thinking 与 final answer 分开
   - thinking 是运行中状态，不应和最终 assistant 正文混成一段历史消息。
   - CarbonRag 对应实现：thinking 片段只作为运行时 UI 数据，不写入 session 正文。
   - 参考点：`rust/crates/runtime/src/conversation.rs` 的消息推进顺序。

5. 非核心信息进入折叠层
   - 聊天主视区要优先给消息流，依据、系统状态、上下文细节都应二级展开。
   - CarbonRag 对应实现：右侧信息层改为抽屉；citations 默认折叠；context 细节点击后再展开。
   - 参考点：`rust/crates/claw-cli/src/input.rs` 与 UI parity 相关布局。

## 如何映射到 CarbonRag

### 1. runtime 的 provider abstraction + streaming
- claw-code 的思路是先把 provider 事件标准化，再交给 session/chat UI。
- CarbonRag 本轮没有重做 provider 架构，但把 ask streaming 事件线正式冻结，避免 UI 直接耦合上游 API 的原始响应格式。

### 2. session state / compaction
- claw-code 的 session state / compaction 重点在“让上下文组织成为运行时能力，而不是页面拼接”。
- CarbonRag 本轮不新增 memory 大模块，只把现有 `session_summary + recent_messages + grounding` 的结果做轻量显性化，提升体感。

### 3. shared defaults vs local overrides
- `CLAW.md` 明确共享默认配置和机器本地覆盖要分层。
- CarbonRag 对应口径继续保持：
  - 共享配置写进仓库模板、稳定分支和文档
  - 本机覆盖留在本地 env / 本地脚本
  - 不把机器状态混进共享主线

## 本轮没借什么

1. 没借 commands / tools / plugins 的扩展面
   - 这轮只修聊天体验，不继续扩业务面。

2. 没借完整 memory system
   - 不做 team memory
   - 不做自动长期记忆抽取
   - 不做 live skill discovery / reload

3. 没借复杂 reasoning 展示
   - 本轮只保留 thinking 承接位与折叠展示，不展示完整思维链产品。

## 本轮结论

CarbonRag V1.1.5 真正借的是 claw-code 对“聊天是运行时组织能力”的处理方式，而不是去追它更宽的工具面。对本轮最有用的三点只有：

- 事件标准化后再渲染
- session compaction 要让用户感知到
- 把非核心信息从主聊天区挪走
