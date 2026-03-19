#!/usr/bin/env python3
"""Regression probe for auto-apply runtime method mismatch.

Checks whether auto-apply task failures contain the known runtime error:
"run_apply_pipeline" missing on BossApplier.

Exit codes:
- 0: PASS (error not detected)
- 1: FAIL (error detected or probe failed)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Optional

import requests

TERMINAL_STATUSES = {"completed", "failed", "stopped"}
KNOWN_ERROR_TOKEN = "run_apply_pipeline"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe auto-apply runtime and fail if run_apply_pipeline missing error appears."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--phone", default="13800138000", help="Phone used by user_profile.phone")
    parser.add_argument("--keywords", default="Python", help="Job search keywords")
    parser.add_argument("--location", default="", help="Job location")
    parser.add_argument("--max-count", type=int, default=1, help="max_count for task")
    parser.add_argument("--poll-interval", type=float, default=3.0, help="Polling interval seconds")
    parser.add_argument("--timeout", type=int, default=90, help="Max seconds to wait for task status")
    parser.add_argument("--captcha-mode", choices=["manual", "abort"], default="abort", help="captcha_mode")
    parser.add_argument("--login-call-timeout", type=int, default=20, help="login_call_timeout seconds")
    parser.add_argument("--task-timeout", type=int, default=120, help="task_timeout seconds")
    return parser.parse_args()


def parse_json(resp: requests.Response) -> Dict[str, Any]:
    try:
        return resp.json()
    except Exception:
        return {"_text": (resp.text or "")[:500]}


def extract_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    if isinstance(payload.get("task"), dict):
        return payload.get("task", {})
    data = payload.get("data")
    if isinstance(data, dict):
        if isinstance(data.get("task"), dict):
            return data.get("task", {})
        return data
    return {}


def collect_errors(task: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(task, dict):
        return errors

    top_error = task.get("error")
    if top_error:
        errors.append(str(top_error))

    progress = task.get("progress")
    if isinstance(progress, dict):
        p_error = progress.get("error")
        if p_error:
            errors.append(str(p_error))

        platform_progress = progress.get("platform_progress")
        if isinstance(platform_progress, dict):
            for _, item in platform_progress.items():
                if isinstance(item, dict) and item.get("error"):
                    errors.append(str(item.get("error")))

    result = task.get("result")
    if isinstance(result, dict):
        r_error = result.get("error")
        if r_error:
            errors.append(str(r_error))

    return errors


def start_task(session: requests.Session, base_url: str, args: argparse.Namespace) -> str:
    payload = {
        "platform": "boss",
        "keywords": args.keywords,
        "location": args.location,
        "max_count": args.max_count,
        "captcha_mode": args.captcha_mode,
        "login_call_timeout": args.login_call_timeout,
        "task_timeout": args.task_timeout,
        "user_profile": {"phone": args.phone},
    }
    resp = session.post(f"{base_url}/api/auto-apply/start", json=payload, timeout=40)
    body = parse_json(resp)
    if resp.status_code != 200:
        print(f"FAIL start status={resp.status_code} body={json.dumps(body, ensure_ascii=False)}")
        return ""

    task_id = ""
    if isinstance(body, dict):
        task_id = str(body.get("task_id") or "").strip()
        if not task_id:
            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            task_id = str(data.get("task_id") or "").strip()

    if not task_id:
        print(f"FAIL start no task_id body={json.dumps(body, ensure_ascii=False)}")
        return ""

    print(f"INFO task started task_id={task_id}")
    return task_id


def stop_task(session: requests.Session, base_url: str, task_id: str) -> None:
    if not task_id:
        return
    try:
        resp = session.post(f"{base_url}/api/auto-apply/stop/{task_id}", timeout=20)
        print(f"INFO stop status={resp.status_code}")
    except Exception as exc:
        print(f"WARN stop failed: {exc}")


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    session = requests.Session()
    task_id = start_task(session, base_url, args)
    if not task_id:
        return 1

    deadline = time.monotonic() + max(10, int(args.timeout))
    last_status = ""
    detected_known_error = False
    observed_errors: List[str] = []

    try:
        while time.monotonic() < deadline:
            resp = session.get(f"{base_url}/api/auto-apply/status/{task_id}", timeout=25)
            body = parse_json(resp)
            if resp.status_code != 200:
                print(f"FAIL status poll status={resp.status_code} body={json.dumps(body, ensure_ascii=False)}")
                return 1

            task = extract_task(body)
            status = str(task.get("status") or "").strip().lower()
            last_status = status

            errors = collect_errors(task)
            for err in errors:
                if err not in observed_errors:
                    observed_errors.append(err)

            token_hit = any(KNOWN_ERROR_TOKEN in err for err in observed_errors)
            if token_hit:
                detected_known_error = True

            print(f"INFO poll status={status or 'unknown'} errors={len(observed_errors)}")
            if status in TERMINAL_STATUSES:
                break
            time.sleep(max(0.5, float(args.poll_interval)))

    finally:
        stop_task(session, base_url, task_id)

    if detected_known_error:
        print("FAIL detected regression: missing run_apply_pipeline on BossApplier")
        for idx, err in enumerate(observed_errors, 1):
            print(f"  error[{idx}]: {err}")
        return 1

    print(f"PASS no run_apply_pipeline regression detected (last_status={last_status or 'unknown'})")
    if observed_errors:
        for idx, err in enumerate(observed_errors, 1):
            print(f"  note[{idx}]: {err}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
