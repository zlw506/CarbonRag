# Session Memory Mapping

## 研究目标

本文件只回答一件事：在 CarbonRag 开始落 session 和单会话记忆基础层时，`claw-code` 里哪些关于 `session / state / memory / skills` 的分层值得借鉴，哪些当前只做预留。

## claw-code 值得借鉴到 CarbonRag 的点

| claw-code 侧概念 | 它解决的问题 | CarbonRag 当前对应位置 | v0.1.7 状态 |
| --- | --- | --- | --- |
| session / state 分离 | 区分“会话容器”和“运行时瞬时状态” | `app.session` 与 `ai_runtime.context_builder` | 已落地基础骨架 |
| runtime 不直接等于路由 | 让对话历史、工具、provider 不堆进接口层 | `POST /api/v1/sessions/{id}/ask` + `orchestrator.run()` | 已落地 |
| memory 需要层次化讨论 | 避免把会话历史、长期记忆和知识库混成一个词 | `session_context` 只做单会话历史 | 已落地边界 |
| skills / tools 不等价于 memory | 技能和记忆是不同运行时层 | `policy_retrieve` 仍是 tool，不是 memory | 已保持 |

## v0.1.7 实际落了什么

- 会话实体已进入 CarbonRag 正式后端结构，而不是继续只停留在 `trace_id`
- ask 已经会消费最近几轮 `session_context`
- 附件入口已绑定到 session，但不参与回答
- `memory_slot` 仍是预留位，没有扩张成长期记忆伪实现

## 当前仍只是预留位的内容

- 跨会话长期 memory
- session 历史自动摘要压缩
- 附件内容解析进入 retrieval
- 以 skills 为中心的行业流程记忆

## 当前结论

CarbonRag 在这轮真正借鉴到的，不是对方的“记忆功能数量”，而是它对 `session / state / memory / skills` 的分层意识。  
v0.1.7 的正确做法是先把单会话历史和会话容器立起来，而不是过早伪造长期 memory。
