# Git Release Flow

## 目的
这份文档用于固定 CarbonRag 的三条分支线，避免把“开发分支”“源码主线”“云端发布线”混在一起。

## 分支角色
- `feature/*`：开发分支，只用于功能开发、本地验证和破坏性试验
- `main`：稳定源码主线，代表已经验收通过的基线
- `release/cloud-stable`：实际部署线，Netlify 和 VPS 都以它为准

## 主线纪律
1. `feature/*` 先开发和本地验证。
2. 通过验收后，再合入 `main`，让 `main` 成为稳定源码 baseline。
3. 只有确认可对外展示、可外部测试的版本，才从 `main` 快进到 `release/cloud-stable`。
4. Netlify 生产部署和 VPS 部署都只盯 `release/cloud-stable`。

## 什么时候允许从 main 推到 release/cloud-stable
- ask / calc / report / knowledge / memory 主链路都可用
- 本地回归通过
- README、部署文档和环境变量口径一致
- 没有明显半成品 UI 或阻断性错误

## 不允许的做法
- 不允许每个 commit 自动上云
- 不允许把 `feature/*` 长期当生产分支
- 不允许让共享云端环境承受日常试错噪声
- 不允许在 `main` 上直接做未验证的大改动

## Netlify 建议
- 生产站点默认盯 `release/cloud-stable`
- `feature/*` 只在必要时做 preview 或手动验证
- `main` 作为可回滚的稳定源码基线，不直接作为部署目标
- 可在 Netlify 后台锁定当前 deploy，避免误自动发布
- 如需跳过某次 Git 驱动发布，可使用团队认可的 skip 约定

## VPS 建议
- 稳定部署目录始终使用同一套路径
- 后端服务只跟 `release/cloud-stable`
- 发布前先执行数据库初始化和健康检查
- 若需要回溯问题，先回查 `main` 对应的稳定源码状态
