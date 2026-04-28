# OpenSpec Adoption Notes

版本：V1.2.1

## 本地试点结果

- Node.js：`v24.11.0`
- npm：`11.6.1`
- OpenSpec 包：`@fission-ai/openspec`
- OpenSpec 版本：`1.3.1`
- 初始化命令：`openspec init --tools codex --profile core .`
- 更新命令：`openspec update .`
- 当前 CLI 配置：`custom` profile，工作流为 `propose / explore / apply / archive`

## 重要发现

- OpenSpec 初始化创建了 `openspec/changes`、`openspec/specs` 和 Codex OpenSpec skills。
- 当前 CLI 没有可直接选择的 extended profile preset；V1.2.1 先按 core/custom 的四步工作流落地。
- `openspec/specs/**` 是人工校验后的 source of truth。
- `openspec/changes/**` 用于 proposed modifications。

## spec-gen 试点结果

- spec-gen 来源：`https://github.com/clay-good/spec-gen`
- 本地路径：`3rdparty/spec-gen`
- 版本：`spec-gen-cli@1.3.4`
- 构建方式：在 `3rdparty/spec-gen` 执行 `npm install`、`npm run build`、`npm link`
- 分析命令：`spec-gen init`、`spec-gen analyze`

## spec-gen 分析摘要

- Files analyzed：364
- Languages：Python、Markdown、TypeScript
- Route inventory：53 routes
- UI inventory：17 components
- Env inventory：20 vars
- 生成目录：`.spec-gen/analysis/`
- 向量索引：因缺少 embedding 配置跳过
- 本地误用的嵌套 `CarbonRag/` 目录已加入忽略范围，避免污染 spec-gen 试点分析。

## 提交边界

- 提交人工校验后的 `openspec/specs/**`。
- 不提交 `.spec-gen/`。
- 不提交 `3rdparty/spec-gen/`。
- 不提交本地模型路径、API key、个人 IDE 配置、agent session 记录。
