# Session Foundation Flow

版本：v0.1.7

## 目标

本轮把 CarbonRag 从“单轮问答页”推进到“最小可用对话工作台”，同时补上 session 持久化、单会话上下文延续和文件上传入口骨架。

## 会话存储结构

当前 session 基座采用本地 SQLite，文件位于：

```text
data/outputs/runtime/carbonrag.sqlite3
```

最小数据模型包括：

- `sessions`
- `messages`
- `files`

其中：

- `sessions` 保存标题和更新时间
- `messages` 保存单会话消息流
- `files` 保存上传附件元信息

## Ask with Session Flow

当前 ask 主链为：

```text
frontend chat workspace
  -> POST /api/v1/sessions/{id}/ask
  -> session service 读取最近 4 轮消息
  -> ai_runtime ask mode
  -> policy_retrieve
  -> context_builder 注入 session history + policy hits
  -> provider
  -> response formatter
  -> session service 回写 user / assistant 消息
  -> frontend 刷新当前 session 消息流与 source panel
```

## Session Context 注入策略

当前只做单会话上下文，不做长期记忆。

上下文顺序固定为：

1. 最近 4 轮会话历史
2. 当前命中的公共政策片段
3. 当前用户问题

当前不做：

- 跨会话共享
- 自动摘要压缩
- 用户画像式长期记忆

## 附件流

当前附件主链为：

```text
frontend file input
  -> POST /api/v1/files
  -> file service 校验文件类型与大小
  -> data/outputs/uploads/{session_id}/
  -> SQLite 记录 file metadata
  -> frontend 刷新当前 session 文件列表
```

本轮附件只进入 session 资产层，不进入 retrieval、embedding、ask。

## 当前边界

- ask 仍只支持 `knowledge_scope=public`
- private / calc / report 继续后置
- 文件上传是入口骨架，不代表文件理解已经完成
