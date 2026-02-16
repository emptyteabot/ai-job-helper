import json
import os
import sys
import time
from typing import Dict

import requests


def check(url: str, path: str, timeout: int = 20, retries: int = 2) -> Dict:
    full = url.rstrip("/") + path
    last_err = ""
    for i in range(max(1, retries)):
        try:
            r = requests.get(full, timeout=timeout)
            return {"path": path, "status": r.status_code, "ok": r.ok, "body": r.text[:240]}
        except Exception as e:
            last_err = str(e)[:240]
            if i < retries - 1:
                time.sleep(0.8)
    return {"path": path, "status": 0, "ok": False, "error": last_err}


def main() -> int:
    base = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000")
    endpoints = ["/api/ping", "/api/version", "/api/ready", "/api/health"]
    rows = [check(base, p) for p in endpoints]
    all_ok = all(x["ok"] for x in rows)
    print(json.dumps({"base": base, "all_ok": all_ok, "checks": rows}, ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
