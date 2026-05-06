# Cross Module Change Protocol

版本：V1.2.1

## 什么时候算跨模块变更

满足任一条件即算跨模块：

- 改动跨越 M1-M8 中两个或更多模块。
- 改动一个模块的 public API、数据库字段、配置键或前端路由，并影响其他模块消费。
- 改动部署、权限、OpenSpec 或发布纪律。

## PR 必填内容

- OpenSpec change-id。
- 影响 specs。
- 影响模块。
- API、DB、权限、部署、provider 行为风险。
- 回归验证项。

## 默认处理顺序

1. 先写 `openspec/changes/<change-id>`。
2. 再落代码或文档。
3. 通过 CI 和人工 review。
4. 合并后按需 archive/sync 到 `openspec/specs/**`。

## 禁止事项

- 不允许把跨模块变更伪装成单模块修复。
- 不允许只改代码不更新规格或治理说明。
- 不允许绕过 PR 直接推 `main`。
