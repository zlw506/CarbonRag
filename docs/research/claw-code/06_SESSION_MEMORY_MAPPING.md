# Session Memory Mapping

## 研究目标

本文件只回答一件事：在 CarbonRag 进入 V1.1.3 之后，`claw-code` 里哪些关于 `session / state / memory / skills` 的分层仍值得借鉴，哪些当前只做预留。

## claw-code 值得借鉴到 CarbonRag 的点

| claw-code 侧概念 | 它解决的问题 | CarbonRag 当前对应位置 | V1.1.3 状态 |
| --- | --- | --- | --- |
| session / state 分离 | 区分“会话容器”和“运行时瞬时状态” | `app.session` 与 `ai_runtime.context_builder` | 已落地基础骨架 |
| runtime 不直接等于路由 | 让对话历史、工具、provider 不堆进接口层 | `POST /api/v1/sessions/{id}/ask` + `orchestrator.run()` | 已落地 |
| memory 需要层次化讨论 | 避免把会话历史、长期记忆和知识库混成一个词 | `session_context` + `session_summary` + `memory_notes` | 已落地边界 |
| skills / tools 不等价于 memory | 技能和记忆是不同运行时层 | `policy_retrieve` / `enterprise_retrieve` / `mixed_retrieve` 仍是 tool，不是 memory | 已保持 |
| state 可以承载“当前会话绑定资产” | 让样例挂接、附件状态和最近 scope 进入受控上下文 | `attached_files`、`knowledge_scope_last_used`、`source_summary` | 已落地 |
| compaction 需要可观测 | 让用户知道上下文是否被压缩 | `memory_state.context_usage_estimate` / `compaction_status` | 已落地 |

## V1.1.3 实际落了什么

- session 已不只是消息容器，还开始承载“当前会话的 summary、压缩状态、挂接资产和最近 scope”
- ask 会先根据估算上下文预算决定是否压缩旧消息，再把最近窗口、summary、grounding 和 memory notes 一起送进运行时
- private sample 的绑定语义继续留在 session，但 memory 仍然不等于知识库
- `memory_notes` 作为 backend-only 用户级长期记忆预留，不进入知识库目录，也不暴露成前端 memory UI

## 当前仍只是预留位的内容

- 跨会话长期 memory
- 团队级 memory / shared state
- 自动从问答中抽取并写入 `memory_notes`
- 附件内容深度解析进入 retrieval
- 以 skills 为中心的行业流程记忆

## 边界结论

CarbonRag 这轮真正借鉴到的，不是“更多功能”，而是把 `session / state / summary / memory / tools / knowledge library` 明确拆开。  
V1.1.3 的正确推进方式是：先让 session 能自动压缩并保留 summary，让 memory_notes 只作为 backend-only 的长期记忆预留，再把真正的长期 memory 留到后续轮次，而不是把这些概念混成一个“记忆功能”。
