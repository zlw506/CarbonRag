# Git Release Flow

## 目的
这份文档用于固定 CarbonRag 从“本地最新开发”到“云端稳定发布”的路径，避免共享云端环境被日常 feature 开发污染。

## 分支纪律
- `feature/*`：代码工程师本地开发与联调
- `release/cloud-stable`：稳定展示与外部测试
- `main`：长期稳定基线，不作为当前默认云端发布分支

## 标准流程
1. 在 `feature/*` 完成开发与本地验证。
2. 通过本地回归后，由项目负责人判断是否达到“可对外展示/可外部测试”标准。
3. 只有达到标准的版本，才允许合入 `release/cloud-stable`。
4. Netlify 从 `release/cloud-stable` 触发生产部署。
5. VPS 后端在 `release/cloud-stable` 上执行 `git pull` 并重启服务。

## 什么时候允许合入 release/cloud-stable
- ask / calc / feedback 主链路可用
- 本地回归通过
- README、部署文档、环境变量口径与代码一致
- 不存在明显半成品 UI 或已知阻断性错误

## 不允许的做法
- 不允许每个 commit 都自动推线上
- 不允许把 `feature/*` 长期当作生产分支
- 不允许本地试验代码直接污染共享云端环境

## Netlify 建议
- 生产站点默认盯 `release/cloud-stable`
- `feature/*` 只在必要时做 preview 或手动验证
- 可在 Netlify 后台锁定当前 deploy，避免误自动发布
- 如需跳过某次 Git 驱动发布，可在提交信息中使用团队认可的 skip 约定

## VPS 建议
- 稳定部署目录始终使用同一套路径
- 后端服务只跟 `release/cloud-stable`
- 发布前先执行数据库初始化和健康检查
