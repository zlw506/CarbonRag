# VPS Backend Deploy

## 目标环境
- 系统：阿里云 Ubuntu VPS
- 部署目录：`/srv/carbonrag/app`
- 后端监听：`127.0.0.1:8000`
- 数据库：PostgreSQL
- Nginx：外部 `80` 转发到 `127.0.0.1:8000`

## 推荐发布分支
- VPS 稳定部署默认使用：`release/cloud-stable`

## 目录要求
- `/srv/carbonrag/app/backend`
- `/srv/carbonrag/app/frontend`
- `/srv/carbonrag/app/data`
- `/srv/carbonrag/shared/uploads`

## 环境变量文件
真实生产值放在：

```bash
/etc/carbonrag/carbonrag.env
```

建议内容：

```env
APP_ENV=production
APP_HOST=127.0.0.1
APP_PORT=8000

MODEL_API_BASE_URL=https://cli-proxy-api-latest-tqjw.onrender.com/v1
MODEL_API_KEY=replace-with-real-model-api-key
MODEL_NAME=gpt-5.4

DATABASE_URL=postgresql://carbonrag_user:CarbonRag666!@127.0.0.1:5432/carbonrag_db
MEMORY_BACKEND=postgres

PUBLIC_DATA_DIR=/srv/carbonrag/app/data/public
PRIVATE_SAMPLE_DIR=/srv/carbonrag/app/data/private_sample
FACTOR_DATA_DIR=/srv/carbonrag/app/data/factors
UPLOAD_DIR=/srv/carbonrag/shared/uploads
```

## 安装命令
只保留这一套标准方案：

```bash
cd /srv/carbonrag/app
git checkout release/cloud-stable
git pull origin release/cloud-stable
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

## 数据库初始化
在服务启动前执行：

```bash
cd /srv/carbonrag/app/backend
/srv/carbonrag/app/.venv/bin/python -m app.runtime_db.bootstrap
```

这一步会按当前 `DATABASE_URL` 建立运行时核心表：
- `sessions`
- `messages`
- `files`
- `session_private_samples`
- `feedback_entries`
- `carbon_calculations`

## systemd
推荐直接使用仓库内模板：

```bash
cp /srv/carbonrag/app/docs/deploy/carbonrag.service /etc/systemd/system/carbonrag.service
systemctl daemon-reload
systemctl enable carbonrag
systemctl restart carbonrag
```

## 启动入口
当前生产入口仍是：

```bash
app.main:app
```

实际启动命令：

```bash
/srv/carbonrag/app/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips='*'
```

本轮先保持单 worker，不额外增加 `--workers`。

## 校验命令
VPS 本机：

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/api/v1/system/info
curl -X POST http://127.0.0.1:8000/api/v1/calc-carbon \
  -H "Content-Type: application/json" \
  -d '{"period_label":"2026-Q1","electricity_kwh":12000,"natural_gas_m3":800,"diesel_l":120}'
curl -X POST http://127.0.0.1:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"target_type":"calc_carbon","trace_id":"deploy-check-trace","rating":"up"}'
```

公网：

```bash
curl http://8.141.111.33/healthz
curl http://8.141.111.33/api/v1/system/info
curl -X POST http://8.141.111.33/api/v1/calc-carbon \
  -H "Content-Type: application/json" \
  -d '{"period_label":"2026-Q1","electricity_kwh":12000,"natural_gas_m3":800,"diesel_l":120}'
curl -X POST http://8.141.111.33/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"target_type":"calc_carbon","trace_id":"deploy-check-trace","rating":"up"}'
```
