# Chat UX and Memory Notes

## 研究范围

本文件只记录 V1.1.4 这轮和聊天体验相关、且仍然值得借鉴的部分：

- `provider abstraction + streaming`
- `session state / compaction`
- `memory / skills / hooks` 与 shared/local 配置边界

本文件不展开插件系统、不展开完整技能生态，也不把 `memory` 误写成知识库。

## 参考输入

- 本地参考：`F:\Project\CarbonRag\CarbonRag\3rdparty\claw-code-study\fix_ui_parity_snapshot`
- 云端参考：`https://github.com/ultraworkers/claw-code/tree/fix/ui-parity`
- 共享配置参考：`F:\Project\CarbonRag\CarbonRag\3rdparty\claw-code-study\main_snapshot\CLAW.md`

本轮只从这三份材料里抽取 runtime 分层、session/compaction、memory 边界与 shared/local 配置治理，不扩散到插件或更广生态。

## claw-code 里值得借的点

| claw-code 概念 | 解决的问题 | CarbonRag 当前映射 | 本轮借鉴情况 |
| --- | --- | --- | --- |
| provider abstraction + streaming | 把模型调用和 UI 渲染解耦 | `OpenAICompatibleChatProvider` + SSE ask route | 已开始借鉴 |
| session state / compaction | 让长对话保持可控上下文 | `session_summary` + `memory_state` + `SessionService.build_session_context()` | 已落地基础，继续增强 |
| memory / skills / hooks 边界 | 避免把对话记忆、工具和知识库混成一个概念 | `memory_notes`、`knowledge_items`、`policy_retrieve` / `enterprise_retrieve` / `mixed_retrieve` | 已明确边界 |
| shared defaults vs local overrides | 共享配置和机器本地覆盖分层 | `.env.production` / `.env.local` / release branch discipline | 已沿用治理思路 |

## 对 CarbonRag 的映射

- `provider abstraction + streaming`
  - 目标不是把 UI 绑定到 provider 的返回字符串，而是让 provider 向 runtime 提供可分流的事件。
  - CarbonRag 本轮要把 `thinking` 和 `answer` 作为不同 UI 状态承接，而不是把“完整文本”当唯一结果。

- `session state / compaction`
  - 目标不是无限堆历史，而是保留最近窗口，再把更早历史压进 `session_summary`。
  - CarbonRag 现在的 memory foundation 仍然是 session 级，不是长期记忆自动写入。

- `memory / skills / hooks`
  - `memory` 只承载对话过程和用户交互上下文。
  - `skills / tools` 只承载任务执行和检索动作。
  - `knowledge library` 只承载知识条目，不等于对话记忆。

- `shared defaults vs local overrides`
  - 仓库模板与稳定分支写共享默认。
  - 本机开发配置继续留给本地 env / 本地脚本。
  - 不把个人机器状态混进共享主线。

## 本轮具体借了什么

- 借了 `session state + compaction` 的分层思想
- 借了 `provider abstraction` 和 streaming 事件的分离思路
- 借了 shared / local 配置治理方法
- 借了“memory 不等于 knowledge library”的边界意识

## 本轮没有借什么

- 没有借完整插件系统
- 没有借 live skill discovery / reload
- 没有借 team-memory 全链路
- 没有借更广的生态集成层

## 结论

CarbonRag 这轮学的不是“更多功能”，而是把聊天工具的运行时分层做清楚：  
`provider` 负责流式输出，`session` 负责上下文组织，`memory` 负责对话连续性，`knowledge library` 负责检索证据。  
这四层要继续分开，不能再混成一个“记忆功能”。
