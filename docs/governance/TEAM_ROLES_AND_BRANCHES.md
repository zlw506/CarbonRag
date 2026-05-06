# Team Roles and Branches

版本：V1.2.1

## #1 首席团队

- 分支：`t1/v1.2/<topic>`
- 仓库：`Git-ys1/CarbonRag`
- 流程：`main -> t1/v1.2/<topic> -> PR -> main`
- 审查：#1 自有代码经自审后可由 `Git-ys1` 最终批准合并。

## #2 第二席团队

- 分支：`t2/v1.2/<topic>`
- 仓库：第二席团队 fork
- 流程：`upstream/main -> fork:t2/v1.2/<topic> -> PR to Git-ys1/CarbonRag:main`
- 审查：必须由 `Git-ys1` 审查代码、规格、模块边界和测试结果。

## main

`main` 是已验收、可运行、可回退的稳定源码基线，也是当前公网默认发布基线。

## release/cloud-stable

`release/cloud-stable` 暂时保留为历史兼容线，不再作为默认发布线。若部署后台仍指向它，应迁移到 `main` 或在部署文档中标记待办。
