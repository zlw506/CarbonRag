# Local Dev vs Cloud Stable

## 这份文档解决什么问题
CarbonRag 从 v0.1.9F 开始，明确采用双环境双节奏：
- `local-dev`：最新开发环境
- `cloud-stable`：稳定展示环境

两者不是同一套运行时，不共享运行时数据库，也不承担同一类职责。

## local-dev
- 用途：代码开发、联调、破坏性验证
- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- 前端 API 基址：`http://127.0.0.1:8000/api`
- 后端数据库：SQLite fallback

启动方式：

Windows：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-local.ps1
```

macOS / Linux：
```bash
bash scripts/dev-local.sh
```

## cloud-stable
- 用途：稳定展示、外部测试、版本验收
- 前端：Netlify
- 后端：VPS
- 前端 API 基址：`/api`
- 后端数据库：PostgreSQL
- 发布分支：`release/cloud-stable`

## 两边数据库是否共享
不共享。

当前固定口径：
- 本地开发：SQLite fallback
- 云端稳定：PostgreSQL

所以这两个现象都属于正常情况：
- 本地聊天记录和云端聊天记录不同
- 云端多个设备能同步会话，而本地和云端不同步

## 为什么历史记录会不同
因为两边不是同一个运行时数据库。

本地：
- 侧重快速开发
- 数据可随时重置
- 不作为外部展示依据

云端：
- 侧重稳定展示
- 供项目负责人和测试者验证
- 不应被未完成 feature 污染

## 哪一边用于什么
- 本地：开发、试错、临时验证
- 云端：稳定展示、外部验证、可回溯版本

## 纪律要求
- 不允许把本地实验数据伪装成稳定结果
- 不允许让共享云端环境承受日常半成品开发噪声
- 云端更新必须通过 `release/cloud-stable`
