# chat-session-controls-title-flow

## Why

CarbonRag 的聊天工作台需要更贴近主流 AI 工具体验：新会话首次发送后应立即生成标题，第二次发送后再修正，之后不再由 AI 自动改名；用户也需要随时手动管理会话。

## What Changes

- 在第一次用户发送后、助手回复前生成临时会话标题。
- 在第二次用户发送后、助手回复前基于第一轮有效问答和第二次用户发送修正标题。
- 第二次之后 AI 不再自动介入标题。
- 新增会话重命名、置顶、删除能力。
- 前端会话栏增加三点菜单，提供重命名、置顶/取消置顶、删除。

## Impact

- Affected specs: `conversation-memory`, `frontend-shell-settings`
- Affected modules: M2 Conversation / Session / Memory, M3 Frontend Chat UX / Theme / Settings
- API impact: `PATCH /api/v1/sessions/{id}` 扩展 `is_pinned`，新增 `DELETE /api/v1/sessions/{id}`
- DB impact: `sessions` 增加 `is_pinned`、`pinned_at`
