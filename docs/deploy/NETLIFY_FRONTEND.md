# Netlify Frontend Deploy

## 目标
只部署前端静态站点，所有生产 API 请求统一走 `/api/*`，再由 Netlify 代理到：

```text
http://8.141.111.33/api/:splat
```

## 仓库与分支
- 仓库：当前 CarbonRag 主仓
- 推荐部署分支：`feature/v0.1.9c-deploy-config` 验证通过后再切稳定分支

## Netlify 配置
仓库根目录已提交 `netlify.toml`，内容已经固定：
- Base directory：`frontend`
- Build command：`npm ci && npm run build`
- Publish directory：`dist`
- `/api/*` 代理到 VPS 后端
- SPA 刷新回退到 `index.html`

## Netlify 后台填写
- Repository：当前 Git 仓库
- Branch to deploy：当前要上线的分支
- Base directory：`frontend`
- Build command：`npm ci && npm run build`
- Publish directory：`dist`

## 生产环境变量
Netlify 生产环境变量至少设置：

```env
VITE_API_BASE_URL=/api
VITE_APP_TITLE=CarbonRag Conversation Workbench
```

## 本地与生产口径
- 本地开发推荐 `.env.local`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

- 生产构建固定：

```env
VITE_API_BASE_URL=/api
```

前端服务层已经改成请求 `/v1/...`，因此：
- 本地会命中 `http://127.0.0.1:8000/api/v1/...`
- 生产会命中 `/api/v1/...`

## 首次上线验证
1. 打开 Netlify 域名首页，确认页面可加载。
2. 打开浏览器开发者工具，确认前端接口请求路径是 `/api/v1/...`，而不是 `127.0.0.1`。
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

## 排错要点
- 如果页面能打开但接口失败，先检查 Netlify 环境变量 `VITE_API_BASE_URL` 是否为 `/api`
- 如果接口返回 502/504，检查 VPS 上 `carbonrag.service` 是否正常运行
- 如果浏览器请求仍指向本地地址，说明构建时仍使用了本地 env，而不是 Netlify 的生产 env
