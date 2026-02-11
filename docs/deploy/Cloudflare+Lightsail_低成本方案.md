# Cloudflare + Lightsail 低成本方案

目标：
- 固定后端成本控制在 `AWS Lightsail $10/月`
- 域名/SSL/CDN 用 Cloudflare 免费层
- 爬虫继续本机运行并推送到云端 API

## 架构

1. `api.yourdomain.com` -> Lightsail Nginx -> Uvicorn(FastAPI)
2. Cloudflare 负责：HTTPS、证书、CDN、WAF基础
3. 本机 `openclaw_crawler_service.py` 定时推送岗位到云端

## A. Lightsail 部署

1. 买 Lightsail 实例（Ubuntu 22.04，$10/月）并绑定 Static IP
2. 上传项目到服务器 `/opt/ai-job-helper`
3. 执行：

```bash
cd /opt/ai-job-helper
sudo bash deploy/lightsail/bootstrap_server.sh
cp deploy/lightsail/env.production.example .env
```

4. 编辑 `.env`：
- `DEEPSEEK_API_KEY`
- `CRAWLER_API_KEY`（与本地 crawler.env 一致）
- `JOB_DATA_PROVIDER=cloud`

5. 安装依赖并启服务：

```bash
cd /opt/ai-job-helper
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

sudo cp deploy/lightsail/ai-job-helper.service /etc/systemd/system/ai-job-helper.service
sudo systemctl daemon-reload
sudo systemctl enable ai-job-helper
sudo systemctl restart ai-job-helper
```

6. Nginx：

```bash
sudo cp deploy/lightsail/nginx.ai-job-helper.conf /etc/nginx/sites-available/ai-job-helper.conf
sudo sed -i 's/api.yourdomain.com/api.example.com/g' /etc/nginx/sites-available/ai-job-helper.conf
sudo ln -sf /etc/nginx/sites-available/ai-job-helper.conf /etc/nginx/sites-enabled/ai-job-helper.conf
sudo nginx -t && sudo systemctl restart nginx
```

## B. Cloudflare 配置

1. 域名接入 Cloudflare
2. DNS 新增：
- `A api` -> Lightsail Static IP，`Proxy = ON`
3. SSL/TLS：
- 模式选 `Full`
- 打开 Always Use HTTPS

验证：
- `https://api.example.com/api/health`
- `https://api.example.com/app`

## C. 本地爬虫推送

本地 `crawler.env`：

```env
CLOUD_API_URL=https://api.example.com
CRAWLER_API_KEY=同服务器.env
CRAWL_INTERVAL_HOURS=6
OPENCLAW_JOB_SITES=boss
```

运行：

```bash
python openclaw_crawler_service.py
```

在 Chrome 打开 Boss 并点击 OpenClaw 扩展 `Attach` 后，才会开始抓取。

验证：
- `https://api.example.com/api/crawler/status` 的 `total` 持续增加

## D. Cloudflare Pages（可选）

如果要单独落地页，可直接用：
- `deploy/cloudflare/pages-public/index.html`

Pages 项目构建目录指向 `deploy/cloudflare/pages-public` 即可。

## E. Worker 反代（可选）

若要让 `api.yourdomain.com` 经 Worker 转发：
- 使用 `deploy/cloudflare/worker-proxy.js`
- 复制 `deploy/cloudflare/wrangler.toml.example` 为 `wrangler.toml`
- 配置 `BACKEND_ORIGIN`

