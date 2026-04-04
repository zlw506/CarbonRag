# CarbonRag Adoption Matrix

## CarbonRag 必须借鉴

| 项目 | 判定理由 |
| --- | --- |
| runtime 与业务接口分层 | 供应商访问、会话、权限、工具调度不能直接混在 `ask` / `calc` / `report` 路由里 |
| provider / runtime / tools / commands 的边界意识 | 这能避免后续功能增长时所有逻辑堆进单一服务层 |
| 将 hooks / skills / plugins 视为三类不同扩展面 | 三者职责不同，若一开始混淆，后续很难治理 |
| 用 parity/gap 文档管理“还缺什么” | CarbonRag 后续 AI Runtime 也需要显式记录缺口，而不是靠口头记忆 |
| 将 session / state / memory 分开讨论 | 这有助于避免把对话历史、知识库和企业私有数据混成一个概念 |

## CarbonRag 暂缓借鉴

| 项目 | 暂缓理由 |
| --- | --- |
| plugin marketplace / install-update-enable-disable 流程 | 当前产品阶段过早，先保留扩展边界即可 |
| 完整 skills registry / bundled skills / reload 机制 | 先做最小业务闭环，再决定是否需要统一技能注册表 |
| 远程 structured transport 与 CLI 宽命令面 | 当前 CarbonRag 入口仍是 Web 产品，不是 coding-agent 终端 |
| LSP、remote runtime、compat-harness 类兼容层 | 这些都属于 runtime 成熟后的增强项 |
| team memory / team workflow 协作层 | 当前仓库和产品都未到多人协同 runtime 阶段 |

## CarbonRag 当前明确不借鉴

| 项目 | 明确不借鉴理由 |
| --- | --- |
| 直接拷贝 `claw-code` 源码进 `backend/app` | 本轮是研究，不是二开或依赖接入 |
| 把 coding-agent CLI 直接当 CarbonRag 产品壳 | CarbonRag 是双碳垂直业务系统，不是终端 coding harness |
| 把静态快照研究包装成“已集成成功” | 这会虚报项目进度，也会误导后续架构决策 |
| 在没有边界设计前先做 plugin / memory / hooks 伪实现 | 先做伪实现只会制造技术债 |
| 为了追求功能数量而复制对方命令宽度 | CarbonRag 当前需要的是稳定垂直闭环，不是 CLI 命令面竞赛 |

## 当前结论

对 CarbonRag 来说，最值得学的是：

- 分层
- 扩展边界
- gap 管理方式

当前最不值得学的是：

- 直接搬代码
- 直接搬产品入口
- 在没有 runtime 设计时先搬表面功能
