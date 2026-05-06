# Git Release Flow

## 目的
这份文档用于固定 CarbonRag 的三条分支线，避免把“开发分支”“源码主线”“云端发布线”混在一起。

## 分支角色
- `t1/v1.2/<topic>`：#1 首席团队开发分支
- `t2/v1.2/<topic>`：#2 fork-and-PR 开发分支
- `feature/*`：历史开发分支或单人试验分支
- `main`：稳定源码主线，也是当前公网默认发布基线
- `release/cloud-stable`：历史兼容发布线，暂时保留但不再作为默认部署目标

## 主线纪律
1. 所有开发先进入 `t1/*`、`t2/*` 或明确批准的 feature 分支。
2. 通过验收后，通过 PR 合入 `main`。
3. `main` 必须保持可运行、可回退、可部署。
4. Netlify 与 VPS 默认跟随 `main`；如仍跟随 `release/cloud-stable`，必须在部署记录中标明迁移待办。

## PR 合并到 main 的条件
- PR 模板完整填写 OpenSpec、模块、风险、验证和批准字段
- CI 通过
- 模块 owner 审查通过
- `Git-ys1` 最终批准
- 必要时使用 squash merge 保持 `main` 历史清晰
- #2/#3 PR 必须说明本地测试结果，至少覆盖 OpenSpec validation 和相关后端/前端检查。

## 不允许的做法
- 不允许每个 commit 自动上云
- 不允许把 `feature/*`、`t1/*` 或 `t2/*` 长期当生产分支
- 不允许让共享云端环境承受日常试错噪声
- 不允许在 `main` 上直接做未验证的大改动

## Netlify 建议
- 生产站点默认盯 `main`
- `t1/*`、`t2/*` 和 `feature/*` 只在必要时做 preview 或手动验证
- `release/cloud-stable` 保留为历史兼容分支
- 可在 Netlify 后台锁定当前 deploy，避免误自动发布
- 如需跳过某次 Git 驱动发布，可使用团队认可的 skip 约定

## VPS 建议
- 稳定部署目录始终使用同一套路径
- 后端服务默认跟 `main`
- 发布前先执行数据库初始化和健康检查
- 若当前 VPS 仍跟 `release/cloud-stable`，先记录迁移状态，再统一到 `main`

## V1.2.5 协作基线
- `main` 必须包含 `AGENTS.md`、`openspec/**`、`.codex/skills/**`、`.github/**`、`docs/governance/**`、`docs/architecture/**`、`scripts/**` 和 env 模板。
- 被忽略的本地资产不得作为“原版”依赖；部署和测试文档必须说明如何重建。
