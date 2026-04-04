# AI Runtime Architecture Freeze

版本：v0.1.4

## 为什么 AI Runtime 要独立于业务接口

CarbonRag 后续一定会有 `ask`、`calc-carbon`、`generate-report` 三类业务接口，但这三类接口不应各自长出一套模型调用、上下文拼接、工具调度和输出包装逻辑。v0.1.4 的核心决策是先冻结统一 AI Runtime，再让未来业务接口只作为外部入口。

这样做的原因只有三个：

- provider 访问需要单点治理，不能分散在不同路由
- mode、context、tool policy、response schema 需要统一约束
- 后续即使业务面扩展，runtime 层也能保持稳定边界

## 五层结构职责

### providers

- 负责消费 `MODEL_*` 与 `EMBEDDING_*` 配置
- 负责封装 chat provider 与 embedding provider
- 未来所有模型访问都必须经过 `factory.py`

### runtime

- 负责 mode resolve、context build、guard check、stub tool invoke、response format
- 当前只落地最小 orchestrator，不承担真实业务逻辑

### tools

- 负责业务工具注册与受控调用
- 本轮只允许双碳业务 stub，不允许通用执行能力

### modes

- 负责定义 ask / carbon / report 三种运行模式
- 每个 mode 固定允许工具集、默认 stub 调度顺序、输出 schema 和 prompt policy 占位

### schemas

- 负责冻结 `ChatRequest`、`ToolCall`、`ToolResult`、`ChatResponse`、`RuntimeResult`
- 后续 ask / calc / report 统一围绕这套骨架扩展

## 从 claw-code 吸收了什么

- 吸收 provider、runtime、tools、commands 分层意识
- 吸收将“产品入口层”和“runtime 核心层”分开的做法
- 吸收通过 parity/gap 文档管理长期缺口的思路
- 吸收对 skills / plugins / memory 先定义边界、再决定是否实现的节奏

## 当前明确没有吸收什么

- 不吸收 coding-agent CLI 作为产品入口
- 不吸收插件系统、hooks runtime、memory 真实现
- 不吸收任意 shell、任意文件写、任意网页抓取和任意系统调用
- 不把 claw-code 的源码、命令宽度或实现细节直接搬入 CarbonRag

## 本轮冻结结论

v0.1.4 不解决业务闭环，它只做一件事：把 CarbonRag 的 AI 入口从“provider 雏形”推进到“可运行、可扩展、可约束的内部 runtime 骨架”。
