# Mixed Scope Ask Flow

## 目标

v0.1.8 的 mixed scope 只解决一件事：让 ask 在一次回答里同时参考公共政策依据和当前 session 已挂接的脱敏企业样例，并明确区分两类来源。

## 请求入口

对外入口保持为：

- `POST /api/v1/sessions/{id}/ask`

请求体中使用：

- `knowledge_scope=mixed`

## 运行步骤

1. 路由读取当前 session 最近消息历史
2. 路由读取当前 session 已挂接的 private sample 集合
3. orchestrator 根据 `knowledge_scope=mixed` 选择 `mixed_retrieve`
4. mixed retriever 同时调用：
   - public policy retriever
   - private sample retriever
5. mixed retriever 按“均衡配额”合并结果：
   - `top_k` 尽量 public/private 平分
   - 奇数余量给 `public_policy`
   - 一侧不足时由另一侧补足
6. context builder 把 session history、public hits、private hits 一起注入系统提示
7. provider 基于上下文回答
8. response formatter 直接用检索结果生成 citations 和 `source_summary`

## 模型约束

mixed scope 下，系统提示要求模型遵守三条：

- 明确区分“政策要求”与“样例现状”
- 不能把企业样例当成政策依据
- 如果任一侧证据不足，只能给出受限说明，不得编造

## citations 结构

mixed 回答中的 citations 允许同时包含：

- `source_type=public_policy`
- `source_type=private_sample`

前端需要能看出两类来源区别，并展示：

- 标题
- 来源标签
- snippet
- source link 或 source 标识

## source_summary

`source_summary` 用于让前端快速感知本次回答引用了多少条不同来源：

```json
{
  "knowledge_scope": "mixed",
  "public_policy_count": 2,
  "private_sample_count": 2,
  "total_citation_count": 4
}
```

## 当前边界

- mixed scope 仍然不是完整 public/private reasoning 平台
- 当前不做用户上传文件解析
- 当前不做自动工具规划
- 当前不做长期 memory 与跨会话推理
