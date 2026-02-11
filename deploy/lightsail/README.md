# Lightsail + Cloudflare Deployment (Budget Plan)

Target stack:
- Backend: AWS Lightsail (`$10/mo`) running FastAPI (`web_app.py`)
- Front proxy + SSL + CDN: Cloudflare (free)
- Optional static landing: Cloudflare Pages (free)
- Local crawler: `openclaw_crawler_service.py` on your PC (pushes jobs to cloud API)

## 1) Lightsail server

Use Ubuntu 22.04 LTS, static IP attached.

Run on server:

```bash
sudo bash /opt/ai-job-helper/deploy/lightsail/bootstrap_server.sh
```

## 2) App files on server

Copy project to server path `/opt/ai-job-helper` (git clone or scp).

Then:

```bash
cd /opt/ai-job-helper
cp deploy/lightsail/env.production.example .env
# edit .env: DEEPSEEK_API_KEY / CRAWLER_API_KEY / other values

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Systemd service

```bash
sudo cp deploy/lightsail/ai-job-helper.service /etc/systemd/system/ai-job-helper.service
sudo systemctl daemon-reload
sudo systemctl enable ai-job-helper
sudo systemctl restart ai-job-helper
sudo systemctl status ai-job-helper --no-pager
```

## 4) Nginx reverse proxy

Edit `deploy/lightsail/nginx.ai-job-helper.conf` server_name then:

```bash
sudo cp deploy/lightsail/nginx.ai-job-helper.conf /etc/nginx/sites-available/ai-job-helper.conf
sudo ln -sf /etc/nginx/sites-available/ai-job-helper.conf /etc/nginx/sites-enabled/ai-job-helper.conf
sudo nginx -t
sudo systemctl restart nginx
```

## 5) Cloudflare DNS + SSL

- Add your domain to Cloudflare.
- Point `api.yourdomain.com` -> Lightsail static IP (`A` record, Proxied).
- SSL/TLS mode: `Full` (or `Full (strict)` after origin cert install).
- Always Use HTTPS: On.

Now backend should be reachable:
- `https://api.yourdomain.com/api/health`
- `https://api.yourdomain.com/app`

## 6) Local crawler to cloud

On your local machine (`crawler.env`):

```env
CLOUD_API_URL=https://api.yourdomain.com
CRAWLER_API_KEY=YOUR_KEY_MATCHING_SERVER_ENV
CRAWL_INTERVAL_HOURS=6
OPENCLAW_JOB_SITES=boss
```

Then run:

```bash
python openclaw_crawler_service.py
```

After Attach + first push:
- `https://api.yourdomain.com/api/crawler/status` should show `total > 0`.

