# AI Runtime Execution Flow

版本：v0.1.4

## 执行主链

```text
API request
  -> mode resolve
  -> context build
  -> tool policy check
  -> stub tool invoke
  -> provider stub invoke
  -> response format
```

## 分步说明

### 1. API request

未来对外接口会把 HTTP 请求转换成内部 `ChatRequest`。v0.1.4 还没有对外业务路由，这一步当前由单元测试与内部调用承担。

### 2. mode resolve

`orchestrator` 根据 `request.mode` 解析到 `ask`、`carbon`、`report` 三种 mode 之一。mode 决定允许工具集、默认 stub 调度顺序和最小 prompt policy。

### 3. context build

`context_builder` 生成结构化占位上下文，当前固定保留：

- `policy_context`
- `enterprise_context`
- `carbon_context`
- `report_context`
- `session_state`
- `memory_slot`

这一步的意义是先给后续知识、会话和企业上下文预留位置，而不是现在就接真实数据。

### 4. tool policy check

`guards.py` 先验证两件事：

- 请求的 mode 是否在 runtime 允许范围内
- 该 mode 默认要调度的工具是否都在白名单里

同时 runtime 明确写死四类禁区：

- shell
- arbitrary file write
- arbitrary web fetch
- arbitrary system call

### 5. stub tool invoke

`ToolRegistry` 负责调度 5 个双碳业务 stub：

- `policy_retrieve`
- `enterprise_retrieve`
- `carbon_factor_lookup`
- `carbon_calc`
- `report_draft`

当前工具只返回固定占位结果，用于证明“未来 AI 通过受控工具工作”，而不是“直接自己做一切”。

### 6. provider stub invoke

chat provider 当前只返回统一的 stub 文本，embedding provider 只保留 descriptor 和最小 stub 能力。本轮不追求真实模型回答闭环。

### 7. response format

`response_formatter` 统一生成 `RuntimeResult`，把上下文摘要、工具调用记录、工具结果和 provider 响应打包成稳定内部结构，供未来业务接口复用。
