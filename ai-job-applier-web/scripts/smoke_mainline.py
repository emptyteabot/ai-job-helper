#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import requests

PASS = "PASS"
ASSISTED = "ASSISTED"
FALLBACK = "FALLBACK"
FAIL = "FAIL"

STATUS_PRIORITY: Dict[str, int] = {
    PASS: 0,
    ASSISTED: 1,
    FALLBACK: 2,
    FAIL: 3,
}
STATUS_ORDER = (PASS, ASSISTED, FALLBACK, FAIL)
PRIORITY_TO_STATUS = {priority: status for status, priority in STATUS_PRIORITY.items()}
READINESS_ENDPOINTS = (
    "/api/providers/readiness",
    "/api/auth/providers",
    "/api/system/readiness",
)
CHANGE_PASSWORD_ENDPOINT = "/api/auth/change-password"


def _extract_local_account(payload: Dict[str, Any]) -> Dict[str, Any] | None:
    if not payload or not isinstance(payload, dict):
        return None
    for section in ("auth", "providers"):
        section_payload = payload.get(section)
        if isinstance(section_payload, dict):
            local_account = section_payload.get("local_account")
            if isinstance(local_account, dict):
                return local_account
    return None


def probe_local_account_availability(
    base_url: str,
    existing_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if existing_payload:
        local_account = _extract_local_account(existing_payload)
        if local_account is not None:
            enabled = local_account.get("enabled")
            if enabled is None:
                enabled = local_account.get("available")
            return {
                "available": bool(enabled) if enabled is not None else True,
                "endpoint": "/api/system/readiness",
                "detail": local_account,
            }
    for endpoint in READINESS_ENDPOINTS:
        if endpoint == "/api/system/readiness" and existing_payload is not None:
            continue
        try:
            payload = request_json("GET", f"{base_url.rstrip('/')}{endpoint}")
        except Exception:
            continue
        local_account = _extract_local_account(payload)
        if local_account is None:
            continue
        enabled = local_account.get("enabled")
        if enabled is None:
            enabled = local_account.get("available")
        return {
            "available": bool(enabled) if enabled is not None else True,
            "endpoint": endpoint,
            "detail": local_account,
        }
    return {"available": True, "endpoint": None, "detail": None}


def _normalize_token(raw: str | None) -> str | None:
    if raw is None:
        return None
    normalized = str(raw).strip()
    return normalized or None


def _rotated_password(password: str) -> str:
    return f"{password}.rotated"


def request_json(method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
    response = requests.request(method, url, timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()


def login_local_account(
    base_url: str,
    email: str,
    password: str,
    register_if_missing: bool,
) -> tuple[Dict[str, Any], str]:
    try:
        payload = request_json(
            "POST",
            f"{base_url.rstrip('/')}/api/auth/local-login",
            json={"email": email, "password": password},
        )
        auth_step = "auth local-login"
    except Exception as exc:
        if not register_if_missing or ("404" not in str(exc) and "401" not in str(exc)):
            raise
        payload = request_json(
            "POST",
            f"{base_url.rstrip('/')}/api/auth/local-register",
            json={"email": email, "password": password},
        )
        auth_step = "auth local-register"
    if payload.get("success") is False:
        raise RuntimeError(payload)
    return payload, auth_step


def upload_resume(base_url: str, token: str, resume_text: str) -> Dict[str, Any]:
    files = {"file": ("resume.txt", resume_text.encode("utf-8"), "text/plain")}
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{base_url}/api/resume/upload", files=files, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Strict smoke for ai-job-applier-web mainline")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default="Acceptance123!")
    parser.add_argument("--keyword", default="Python backend")
    parser.add_argument("--city", default="Shenzhen")
    parser.add_argument("--token", default=None, help="Bearer token used to bypass local account login when disabled")
    parser.add_argument(
        "--status-report",
        default="scripts/.status/smoke_mainline.json",
        help="JSON file that captures the counts and overall status",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.email:
        args.email = f"smoke-{int(time.time())}@agenthelpjob.com"
    base_dir = Path(__file__).resolve().parent
    repo_root = base_dir.parent
    status_report_path = Path(args.status_report)
    if not status_report_path.is_absolute():
        status_report_path = repo_root / status_report_path

    records: List[Dict[str, str]] = []
    counts: Counter[str] = Counter()
    summary_lines: List[str] = []
    highest_priority = STATUS_PRIORITY[PASS]
    hard_failed = False
    token = ""

    def emit(status: str, message: str, summary_note: str | None = None) -> None:
        nonlocal highest_priority
        print(f"[{status}] {message}")
        records.append({"status": status, "message": message})
        counts[status] += 1
        highest_priority = max(highest_priority, STATUS_PRIORITY.get(status, 0))
        if summary_note:
            summary_lines.append(summary_note)

    def write_report() -> None:
        overall = PRIORITY_TO_STATUS.get(highest_priority, PASS)
        if not records:
            print("No steps executed.")
        else:
            print("\nSUMMARY")
            for status in STATUS_ORDER:
                if counts.get(status):
                    print(f"  {status}: {counts[status]}")
            print(f"Overall status: {overall}")
        if summary_lines:
            print("\nSummary")
            for item in summary_lines:
                print(f"- {item}")
        payload = {
            "overall_status": overall,
            "counts": dict(counts),
            "records": list(records),
            "summary_lines": summary_lines,
        }
        status_report_path.parent.mkdir(parents=True, exist_ok=True)
        status_report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_readiness_summary(readiness: Dict[str, Any]) -> None:
        jobs_provider = readiness.get("jobs", {}).get("provider")
        boss_assisted = readiness.get("boss", {}).get("assisted_only")
        summary_lines.append(
            f"readiness: jobs.provider={jobs_provider} boss.assisted={boss_assisted}"
        )

    try:
        try:
            readiness = request_json("GET", f"{args.base_url.rstrip('/')}/api/system/readiness")
            emit(PASS, "system readiness endpoint reachable")
            add_readiness_summary(readiness)
        except Exception as exc:
            emit(FAIL, f"system readiness failed: {exc}")
            return 1

        token_override = _normalize_token(args.token)
        if token_override:
            token = token_override
            emit(ASSISTED, "auth token override")
        else:
            try:
                login, auth_step = login_local_account(
                    args.base_url,
                    args.email,
                    args.password,
                    register_if_missing=True,
                )
                token = login["token"]
                emit(PASS, auth_step)
            except Exception as exc:
                emit(FAIL, f"auth failed: {exc}")
                return 1

            next_password = _rotated_password(args.password)
            try:
                changed = request_json(
                    "POST",
                    f"{args.base_url.rstrip('/')}{CHANGE_PASSWORD_ENDPOINT}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"current_password": args.password, "new_password": next_password},
                )
                if changed.get("success") is False:
                    raise RuntimeError(changed)
                emit(PASS, "auth change-password")

                relogin, _ = login_local_account(
                    args.base_url,
                    args.email,
                    next_password,
                    register_if_missing=False,
                )
                token = relogin["token"]
                emit(PASS, "auth login after password change")

                restored = request_json(
                    "POST",
                    f"{args.base_url.rstrip('/')}{CHANGE_PASSWORD_ENDPOINT}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"current_password": next_password, "new_password": args.password},
                )
                if restored.get("success") is False:
                    raise RuntimeError(restored)
                emit(PASS, "auth restore-password")

                restored_login, _ = login_local_account(
                    args.base_url,
                    args.email,
                    args.password,
                    register_if_missing=False,
                )
                token = restored_login["token"]
                emit(PASS, "auth login after restore")
            except Exception as exc:
                emit(FAIL, f"auth change-password failed: {exc}")
                return 1

        resume_text = "Python FastAPI Redis Docker\n3 years experience\nShenzhen"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            upload = upload_resume(args.base_url.rstrip("/"), token, resume_text)
            if not upload.get("success"):
                raise RuntimeError(upload)
            emit(PASS, "resume upload")
            resumes = request_json("GET", f"{args.base_url.rstrip('/')}/api/resume/list", headers=headers)
            if not resumes.get("resumes"):
                raise RuntimeError("resume list empty")
            emit(PASS, "resume list")
        except Exception as exc:
            emit(FAIL, f"resume flow failed: {exc}")
            return 1

        try:
            hr_job = request_json(
                "POST",
                f"{args.base_url.rstrip('/')}/api/hr/jobs",
                json={
                    "hr_id": "hr-demo",
                    "title": "Python Backend Engineer",
                    "company": "AgentHelpJob",
                    "location": args.city,
                    "skills": ["python", "fastapi", "redis"],
                    "min_years": 2,
                },
            )
            job_id = hr_job["job"]["job_id"]
            matches = request_json(
                "GET",
                f"{args.base_url.rstrip('/')}/api/hr/candidates/match",
                params={"job_id": job_id, "hr_id": "hr-demo"},
            )
            if not matches.get("candidates"):
                raise RuntimeError("candidate match empty")
            emit(PASS, "hr job create + match")
        except Exception as exc:
            emit(FAIL, f"hr flow failed: {exc}")
            return 1

        try:
            jobs = request_json(
                "GET",
                f"{args.base_url.rstrip('/')}/api/jobs/search",
                params={"keyword": args.keyword, "city": args.city, "max_count": 5},
            )
            provider = jobs.get("provider")
            total = int(jobs.get("total") or 0)
            warning = jobs.get("warning") or "<none>"
            if total <= 0:
                emit(FAIL, "jobs/search returned zero jobs")
                hard_failed = True
                return 1
            if provider == "fallback":
                emit(FALLBACK, f"jobs/search returned fallback provider: {warning}")
                summary_lines.append("jobs: partial (fallback)")
            elif provider == "openclaw_challenge":
                emit(ASSISTED, f"jobs/search issued OpenClaw challenge: {warning}")
                summary_lines.append("jobs: assisted (challenge required)")
            else:
                emit(PASS, f"jobs/search provider={provider} total={total}")
                summary_lines.append(f"jobs: live-ish ({provider})")
        except Exception as exc:
            emit(FAIL, f"jobs/search failed: {exc}")
            hard_failed = True

        try:
            boss = request_json("GET", f"{args.base_url.rstrip('/')}/api/boss/status")
            if not boss.get("available"):
                emit(FAIL, "boss bridge unavailable")
                hard_failed = True
            elif boss.get("assisted_only"):
                emit(ASSISTED, "boss bridge is assisted-only; captcha/QR still require human intervention")
                summary_lines.append("boss: assisted")
            else:
                emit(PASS, "boss bridge fully available")
                summary_lines.append("boss: full")
        except Exception as exc:
            emit(FAIL, f"boss status failed: {exc}")
            hard_failed = True

        return 1 if hard_failed else 0
    finally:
        write_report()


if __name__ == "__main__":
    sys.exit(main())
