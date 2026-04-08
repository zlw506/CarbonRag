# Session Memory Mapping

## 研究目标

本文件只回答一件事：在 CarbonRag 已经落下 session、单会话记忆和 session-attached sample 之后，`claw-code` 里哪些关于 `session / state / memory / skills` 的分层仍值得借鉴，哪些当前只做预留。

## claw-code 值得借鉴到 CarbonRag 的点

| claw-code 侧概念 | 它解决的问题 | CarbonRag 当前对应位置 | v0.1.8 状态 |
| --- | --- | --- | --- |
| session / state 分离 | 区分“会话容器”和“运行时瞬时状态” | `app.session` 与 `ai_runtime.context_builder` | 已落地基础骨架 |
| runtime 不直接等于路由 | 让对话历史、工具、provider 不堆进接口层 | `POST /api/v1/sessions/{id}/ask` + `orchestrator.run()` | 已落地 |
| memory 需要层次化讨论 | 避免把会话历史、长期记忆和知识库混成一个词 | `session_context` 只做单会话历史 | 已落地边界 |
| skills / tools 不等价于 memory | 技能和记忆是不同运行时层 | `policy_retrieve` / `enterprise_retrieve` / `mixed_retrieve` 仍是 tool，不是 memory | 已保持 |
| state 可以承载“当前会话绑定资产” | 让样例挂接、附件状态和最近 scope 进入受控上下文 | `attached_files`、`knowledge_scope_last_used`、`source_summary` | 已落地 v0.1.8 |

## v0.1.8 实际落了什么

- session 已不只是消息容器，还开始承载“当前会话挂接了哪些 private sample”
- ask 已能在单会话历史基础上切换 `public / private_sample / mixed`
- private sample 的绑定语义进入 session，而不是散落在前端局部状态里
- `source_summary` 进入会话状态，为后续更复杂的上下文压缩和 memory summary 预留位置

## 当前仍只是预留位的内容

- 跨会话长期 memory
- session 历史自动摘要压缩
- 附件内容解析进入 retrieval
- 以 skills 为中心的行业流程记忆
- 用户画像、团队记忆和跨任务共享 state

## 当前结论

CarbonRag 在这轮真正借鉴到的，不是对方“功能更多”，而是它把 `session / state / memory / tools` 明确拆层。  
v0.1.8 的正确推进方式是：先让 session 能绑定样例、ask 能消费单会话历史和当前 scope，再把长期 memory 留到后续轮次，而不是把这些概念混成一个“记忆功能”。
