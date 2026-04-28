# Module Boundary Map

版本：V1.2.1

## 模块冻结

| 模块 | 名称 | Owner | 职责 |
| --- | --- | --- | --- |
| M1 | AI Runtime / Provider / Model Config | Git-ys1 | 模型调用、provider 切换、自定义 API、Ollama、OpenAI-compatible、重连、timeout、streaming、thinking |
| M2 | Conversation / Session / Memory | Git-ys1 | 会话、ask、ask stream、标题生成、session summary、memory notes、context compaction |
| M3 | Frontend Chat UX / Theme / Settings | Git-ys1 | AskPage、聊天体验、输入框、主题系统、通用设置、响应式、用户偏好 |
| M4 | Auth / User / Admin Governance | Git-ys1 | 注册登录、用户隔离、角色、管理员后台、权限、普通用户与管理员入口隔离 |
| M5 | Knowledge / File / RAG | Git-ys1 | 文件上传、个人知识库、共享知识库、knowledge task、private/mixed retrieval、scan/rebuild/retry |
| M6 | Carbon / Report / Feedback | Git-ys1 | 碳核算、报告生成、报告编辑、反馈回流、输出型业务能力 |
| M7 | DevOps / CI / Release | Git-ys1 | GitHub Actions、VPS 更新脚本、Netlify、环境变量、部署文档、回滚 |
| M8 | Spec / Governance / Project Docs | Git-ys1 | OpenSpec、spec-gen、模块边界、PR 模板、CODEOWNERS、团队纪律、版本纪律 |

## 使用规则

- 每个 PR 必须在模板中勾选影响模块。
- 涉及两个及以上模块时，必须说明跨模块数据流和回滚影响。
- 影响 M4、M7、M8 的 PR 必须由 `Git-ys1` 最终批准。
- #2 用户进入后，在 CODEOWNERS 中追加真实 GitHub 用户名，不替换 `Git-ys1` 最终 owner。
