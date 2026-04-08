# Private Sample Data

`data/private_sample/` 只用于存放脱敏、演示用途的企业样例。

本目录的使用边界：

- 这里只放可公开进仓库的脱敏样例，不放真实企业原始数据。
- 不放真实公司名称、真实地址、真实合同、真实账单、真实员工信息、真实客户信息。
- v0.1.8 的目的只是验证 `private_sample` / `mixed` retrieval，不是接真实企业平台。
- 后续真实企业接入不会直接复用当前仓库内的样例文件与目录结构。

当前样例分为两类：

- `corpus/docs/`：脱敏背景说明、设备与项目概况等 Markdown 文档。
- `corpus/tables/`：脱敏的能耗、产量、物流样例表。

这些样例只用于：

- session 下的样例挂接
- private retrieval
- mixed public/private ask 验证

本轮不做：

- 真实企业数据接入
- 附件深度解析
- calc-carbon 公式求解
- report 生成
