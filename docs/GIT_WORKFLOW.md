# Git 工作流
版本：V1.1.3

## 分支角色
- `main`：稳定源码 baseline
- `feature/*`：功能开发、本地验证、破坏性试验
- `release/cloud-stable`：唯一云端稳定发布线
- `hotfix/*`：最小紧急修复

## 强制规则
- 开工前先做 checkpoint
- 不在脏工作树上叠改
- 不把 key 和敏感数据提交进仓库
- 不把本地实验数据当成稳定结果
- 不允许每个 feature commit 自动推云端
- Netlify 与 VPS 的稳定部署默认都只跟 `release/cloud-stable`

## 本地与云端的关系
- 本地环境服务于快速开发、试错和回归
- 云端环境服务于稳定展示和外部验证
- 本地运行时数据库与云端运行时数据库不共享
- 如果本地和云端历史记录不同，默认视为正常现象

## 主线与发布线
- `main` 是每个阶段验收通过后的稳定源码 baseline
- `release/cloud-stable` 是实际部署线
- `feature/*` 负责把新功能先做出来
- 不让 `feature/*` 直接长期承载云端发布

## 提交格式
- `checkpoint: before v0.x.x`
- `v0.x.x: <内容摘要>`
