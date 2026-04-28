# Netlify Frontend Deploy

## 目标
只部署前端静态站点。生产环境下，所有 API 请求统一走 `/api/*`，再由 Netlify 代理到 VPS 后端。

当前生产代理目标：

```text
http://8.141.111.33/api/:splat
```

## 推荐发布分支
- 生产站点默认盯：`main`
- `t1/*`、`t2/*` 和 `feature/*` 只用于必要的 preview 或手动验证
- `release/cloud-stable` 暂时保留为兼容线，不再作为默认发布分支

## 仓库配置
仓库根目录已提交 `netlify.toml`，当前固定为：
- Base directory：`frontend`
- Build command：`npm ci && npm run build`
- Publish directory：`dist`
- `/api/*` 代理到 VPS 后端
- SPA 刷新回退到 `index.html`

## Netlify 后台填写
- Repository：当前 Git 仓库
- Branch to deploy：`main`
- Base directory：`frontend`
- Build command：`npm ci && npm run build`
- Publish directory：`dist`

## 生产环境变量
至少设置：

```env
VITE_API_BASE_URL=/api
VITE_APP_TITLE=CarbonRag Conversation Workbench
```

## 本地与生产口径
- 本地开发使用 `frontend/.env.local`

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

- 生产构建使用 `frontend/.env.production` 或 Netlify 后台环境变量

```env
VITE_API_BASE_URL=/api
```

前端服务层已经固定请求 `/v1/...`，因此：
- 本地开发命中 `http://127.0.0.1:8000/api/v1/...`
- 生产命中 `/api/v1/...`

## 首次上线验证
1. 打开 Netlify 域名首页，确认页面可加载。
2. 检查浏览器网络请求，确认 API 路径是 `/api/v1/...`，而不是 `127.0.0.1`。
3. 验证 ask：

```text
POST /api/v1/sessions/{id}/ask
```

4. 验证 calc：

```text
POST /api/v1/calc-carbon
```

5. 验证 feedback：

```text
POST /api/v1/feedback
```

## 发布纪律建议
- 生产发布只从 `main` 触发
- 不要让每个 feature commit 自动上云
- 如需暂时冻结线上版本，可在 Netlify 后台锁定当前 deploy
- 如需验证 feature 分支，只做临时 preview，不替代稳定站点
