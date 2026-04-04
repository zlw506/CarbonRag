# src Surface Map

## src/ 的角色判断

主快照中的 `src/` 是一个更宽的成熟产品表面，不只是单个 CLI 入口，而是把 assistant、services、skills、hooks、plugins、state、memdir、cli 等都放在同一棵 Python-first 工作树下。

这意味着：

- Rust workspace 更接近当前 active core
- `src/` 更接近“完整产品表面”和“能力目录索引”

## 重点目录解释

| 目录 | 当前观察到的职责 | 对 CarbonRag 的借鉴点 |
| --- | --- | --- |
| `src/assistant` | agentic loop 与会话表面 | assistant 逻辑应独立于业务接口 |
| `src/services` | API、OAuth、MCP 等服务层汇总 | 服务层应是运行时支撑，不是页面拼装层 |
| `src/skills` | skill 加载、bundled skills、技能发现 | skill 不只是 prompt 文件，还涉及发现、注册、热更新 |
| `src/hooks` | hook 命令与行为入口 | hook 是运行时治理点，不应晚于工具系统思考 |
| `src/plugins` | builtin/bundled/plugin lifecycle | plugin 的关键不是 UI，而是安装、启停、扩展契约 |
| `src/state` | 本地状态和工作态持久化 | 会话状态与业务数据应分开建模 |
| `src/memdir` | memory / session 辅助表面 | memory 不是向量库同义词，而是运行时上下文层 |
| `src/cli` | structured IO、remote IO、handlers | 入口层和 transport 层应与 runtime 内核解耦 |

## src/ 给 CarbonRag 的直接提示

### 1. “业务系统”与“AI runtime”不是一层

CarbonRag 当前是垂直业务系统，但后续 AI Runtime 仍需要单独的中间层。`src/assistant`、`src/services`、`src/state` 这类划分说明，不能把所有模型调用逻辑直接塞进 `ask` 路由。

### 2. skills / hooks / plugins 是三类不同边界

从目录面就能看出：

- `skills` 偏知识和流程片段
- `hooks` 偏运行时切面
- `plugins` 偏可安装扩展

CarbonRag 后续如果引入这些能力，不能混成一个“扩展系统”大杂烩。

### 3. memdir / state 值得单独看待

这两个目录提醒我们：

- memory 是 runtime 上下文组织问题
- state 是会话与本地工作态问题

它们都不等于 CarbonRag 的政策知识库或企业样例数据目录。

## 本轮不延伸的事项

- 不从 `src/` 推导 CarbonRag 具体接口设计
- 不把 `src/` 里的能力当成本轮要落地的功能清单
- 不因为看到 `src/plugins`、`src/memdir` 就在当前仓库里先做伪实现
