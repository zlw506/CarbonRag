# Git 工作流
版本：V1.2.1

## 分支角色
- `main`：稳定源码 baseline，也是当前公网默认发布基线
- `t1/v1.2/<topic>`：#1 首席团队开发分支
- `t2/v1.2/<topic>`：#2 fork-and-PR 开发分支
- `feature/*`：历史或单人试验分支
- `release/cloud-stable`：历史兼容发布线
- `hotfix/*`：最小紧急修复

## 强制规则
- 开工前先做 checkpoint
- 不在脏工作树上叠改
- 不把 key 和敏感数据提交进仓库
- 不把本地实验数据当成稳定结果
- 不允许每个 feature commit 自动推云端
- Netlify 与 VPS 的默认部署口径统一为 `main`
- 所有进入 `main` 的改动必须走 PR、CI、模块 owner review 和 `Git-ys1` 最终批准

## 本地与云端的关系
- 本地环境服务于快速开发、试错和回归
- 云端环境服务于稳定展示和外部验证
- 本地运行时数据库与云端运行时数据库不共享
- 如果本地和云端历史记录不同，默认视为正常现象

## 主线与发布线
- `main` 是每个阶段验收通过后的稳定源码 baseline
- `main` 是当前实际发布基线
- `release/cloud-stable` 只作为兼容线保留
- `t1/*`、`t2/*` 和 `feature/*` 负责把新功能先做出来
- 不让开发分支直接长期承载云端发布

## OpenSpec 纪律
- `openspec/specs/**` 是当前行为规格库
- `openspec/changes/**` 是 proposed changes
- 新功能默认先有 change-id，再施工
- spec-gen 产物只能作为 draft，人工校验后才能进入 specs

## 新席位测试纪律
- #2/#3 从 `upstream/main` 开始，不从 #1 的本机目录复制。
- 忽略文件由模板、脚本或依赖安装重建。
- 本地测试先跑 `openspec validate --all`，再跑 bootstrap、后端 pytest、前端 typecheck/build。
- PR 中必须说明无法运行的验证项及原因。

## 提交格式
- `checkpoint: before v0.x.x`
- `v0.x.x: <内容摘要>`
- `checkpoint: before v1.2.x`
- `v1.2.x: <内容摘要>`
