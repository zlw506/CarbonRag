# Multi-Team Development Discipline

版本：V1.2.1

## 团队口径

- #1 首席团队：可在主仓库创建 `t1/*` 分支，但仍必须走 PR。
- #2 第二席团队：初期走 fork-and-PR，不直接授予主仓库写权限。
- `Git-ys1`：云端 `main` 最终管理员、PR 最终审查人、CODEOWNERS 初版唯一 owner。

## 分支命名

- `t1/v1.2/<topic>`
- `t2/v1.2/<topic>`
- `hotfix/t1/v1.2/<topic>`
- `hotfix/t2/v1.2/<topic>`
- `review/t1/<topic>`
- `review/t2/<topic>`

不要在真实 Git 分支名中使用 `#1` 或 `#2`。

## 合并纪律

- `main` 只接受 PR 合并。
- PR 必须填写 OpenSpec、模块、风险、验证和批准字段。
- 推荐 squash merge，保持 `main` 历史干净。
- #2 或其他用户提交必须由 `Git-ys1` 审查后才能进入 `main`。
