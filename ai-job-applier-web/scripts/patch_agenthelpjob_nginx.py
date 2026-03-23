from __future__ import annotations

from pathlib import Path
import datetime
import shutil


NGINX_CONF = Path("/etc/nginx/sites-enabled/agenthelpjob.com.conf")


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing block: {old.splitlines()[0]}")
    return text.replace(old, new, 1)


def main() -> None:
    text = NGINX_CONF.read_text(encoding="utf-8")
    backup = NGINX_CONF.with_name(
        NGINX_CONF.name + ".bak_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    shutil.copy2(NGINX_CONF, backup)

    text = replace_once(
        text,
        "location /api/ {\n        proxy_pass http://127.0.0.1:8000;",
        "location /api/ {\n        proxy_pass http://127.0.0.1:8766;",
    )
    text = replace_once(
        text,
        "location /docs {\n        proxy_pass http://127.0.0.1:8000/docs;",
        "location /docs {\n        proxy_pass http://127.0.0.1:8766/docs;",
    )
    text = replace_once(
        text,
        "location /openapi.json {\n        proxy_pass http://127.0.0.1:8000/openapi.json;",
        "location /openapi.json {\n        proxy_pass http://127.0.0.1:8766/openapi.json;",
    )
    text = replace_once(
        text,
        "location = / {\n        return 302 /enter;\n    }",
        """location = / {
        proxy_pass http://127.0.0.1:8766;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection upgrade;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }""",
    )
    text = replace_once(
        text,
        "location = /app {\n        proxy_pass http://127.0.0.1:8000/app;",
        "location = /app {\n        proxy_pass http://127.0.0.1:8766/app;",
    )
    text = replace_once(
        text,
        "location = /app_hr {\n        proxy_pass http://127.0.0.1:8000/app_hr;",
        "location = /app_hr {\n        proxy_pass http://127.0.0.1:8766/app_hr;",
    )
    text = replace_once(
        text,
        "location = /app_clean.html {\n        proxy_pass http://127.0.0.1:8000/app_clean.html;",
        "location = /app_clean.html {\n        proxy_pass http://127.0.0.1:8766/app_clean.html;",
    )
    text = replace_once(
        text,
        "location = /auto_apply_panel.html {\n        proxy_pass http://127.0.0.1:8000/auto_apply_panel.html;",
        "location = /auto_apply_panel.html {\n        proxy_pass http://127.0.0.1:8766/auto_apply_panel.html;",
    )
    text = replace_once(
        text,
        "location / {\n        proxy_pass http://127.0.0.1:3001;",
        "location / {\n        proxy_pass http://127.0.0.1:8766;",
    )

    NGINX_CONF.write_text(text, encoding="utf-8")
    print(str(backup))


if __name__ == "__main__":
    main()
