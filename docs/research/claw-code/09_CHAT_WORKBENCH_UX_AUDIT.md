# V1.1.7 Chat Workbench UX Audit Notes

本轮继续强制参考 `3rdparty/claw-code-study`，但只收窄到聊天体验本身，不扩到新的后台能力或插件面。

## 主要参考基线

- `3rdparty/claw-code-study/fix_ui_parity_snapshot/README.md`
- `3rdparty/claw-code-study/fix_ui_parity_snapshot/PARITY.md`
- `3rdparty/claw-code-study/main_snapshot/CLAW.md`

## 本轮借了什么

### 1. 聊天区必须成为中心，而不是被壳层包围

- `fix/ui-parity` 的材料持续强调 streaming、session state 和消息流是核心体验，外围信息应退居二级。
- CarbonRag 本轮对应落点：
  - Ask 页默认进入 focus mode
  - 全局导航在聊天页压成 icon rail
  - 右侧依据/系统状态保持抽屉式按需打开
  - 中间消息列扩大为主视觉区

### 2. streaming 要让用户“感到”系统在工作

- `PARITY.md` 里对 streaming support、session events 和 provider abstraction 的强调，说明体验不只是接口支持，而是事件如何驱动 UI。
- CarbonRag 本轮对应落点：
  - 继续沿用现有 `ask/stream` 契约
  - 不重做后端，只把前端状态机做得更可感知
  - `pending / thinking / streaming / done` 在消息气泡里成为明确状态，而不是轻微小标记

### 3. thinking 与 answer 要分层

- `claw-code` 的 streaming 事件类型和 thinking delta 处理说明：thinking 是运行时状态，不应和最终回答混成一块。
- CarbonRag 本轮对应落点：
  - thinking 继续只在运行中 UI 中出现
  - 最终 assistant 正文和 thinking 分开展示
  - 未返回 reasoning chunk 时也保留明确的“思考中”动画占位

### 4. shared defaults vs local overrides 继续保持分层

- `CLAW.md` 明确要求共享默认配置放仓库、机器本地覆盖留本地。
- CarbonRag 本轮对应落点：
  - 共享 UI 规则、focus mode 口径和 QA checklist 进仓库文档
  - 不把本机调试偏好写进共享实现

## 本轮没借什么

### 1. 没借 commands / tools / plugins 的扩展面

- 本轮不是功能扩张轮。
- 不继续扩 slash commands、插件系统或更多后台能力。

### 2. 没借完整 memory system

- 不做长期 memory 自动写入
- 不做 team memory
- 不做新的 memory 管理界面

### 3. 没借完整的工程化终端交互层

- 不复刻 `compat-harness`
- 不复刻 CLI renderer
- 本轮只借“聊天区层级”和“streaming 事件如何体现在 UI 上”

## 映射结论

V1.1.7 真正向 `claw-code-study` 学的，不是更宽的工具生态，而是这三条：

- 消息流必须压过壳层和元数据
- streaming / thinking 必须让用户有明显体感
- 共享默认与本地覆盖要继续治理分层

本轮因此只做 Ask 页和壳层的产品感打磨，不继续扩业务面。
