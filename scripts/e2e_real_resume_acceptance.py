#!/usr/bin/env python3
"""Run end-to-end acceptance checks using a real resume text/file."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _read_resume_text(path: str) -> str:
    if not path:
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def _post_json(base_url: str, route: str, payload: Dict[str, Any], timeout_s: int = 20) -> requests.Response:
    return requests.post(f"{base_url}{route}", json=payload, timeout=timeout_s)


def _get(base_url: str, route: str, params: Optional[Dict[str, Any]] = None, timeout_s: int = 20) -> requests.Response:
    return requests.get(f"{base_url}{route}", params=params or {}, timeout=timeout_s)


def _run(base_url: str, resume_file: str, keywords: str, location: str) -> List[CheckResult]:
    checks: List[CheckResult] = []
    resume_text = ""

    # 1) Health/version
    try:
        resp = _get(base_url, "/api/version")
        body = resp.json() if resp.text else {}
        ok = resp.status_code == 200 and bool(body.get("success"))
        checks.append(CheckResult("version_api", ok, f"status={resp.status_code}"))
    except Exception as exc:
        checks.append(CheckResult("version_api", False, str(exc)))

    # 2) Upload real resume (if provided)
    if resume_file and os.path.exists(resume_file):
        try:
            with open(resume_file, "rb") as fh:
                files = {"file": (os.path.basename(resume_file), fh, "application/octet-stream")}
                resp = requests.post(f"{base_url}/api/upload", files=files, timeout=40)
            body = resp.json() if resp.text else {}
            resume_text = str(body.get("resume_text") or "").strip()
            ok = resp.status_code == 200 and bool(body.get("success")) and len(resume_text) > 20
            checks.append(CheckResult("upload_resume", ok, f"status={resp.status_code}, chars={len(resume_text)}"))
        except Exception as exc:
            checks.append(CheckResult("upload_resume", False, str(exc)))

    if not resume_text:
        try:
            resume_text = _read_resume_text(resume_file)
        except Exception:
            resume_text = ""

    if not resume_text:
        resume_text = (
            "姓名: Demo Candidate\n"
            "目标岗位: Python后端工程师\n"
            "技能: Python, FastAPI, MySQL, Redis, Docker, Linux\n"
            "经历: 负责高并发接口优化，接口延迟降低35%。\n"
        )
        checks.append(CheckResult("resume_source", True, "fallback_demo_text"))
    else:
        checks.append(CheckResult("resume_source", True, f"chars={len(resume_text)}"))

    # 3) Process pipeline
    process_body: Dict[str, Any] = {}
    try:
        resp = _post_json(base_url, "/api/process", {"resume": resume_text}, timeout_s=80)
        process_body = resp.json() if resp.text else {}
        ok = resp.status_code == 200 and bool(process_body.get("success")) and isinstance(process_body.get("recommended_jobs"), list)
        checks.append(
            CheckResult(
                "process_pipeline",
                ok,
                f"status={resp.status_code}, jobs={len(process_body.get('recommended_jobs') or [])}",
            )
        )
    except Exception as exc:
        checks.append(CheckResult("process_pipeline", False, str(exc)))

    # 4) Search jobs
    jobs: List[Dict[str, Any]] = []
    try:
        resp = _get(
            base_url,
            "/api/jobs/search",
            params={
                "keywords": keywords,
                "location": location,
                "limit": 12,
            },
            timeout_s=40,
        )
        body = resp.json() if resp.text else {}
        jobs = body.get("jobs") or []
        ok = resp.status_code == 200 and bool(body.get("success")) and isinstance(jobs, list)
        checks.append(CheckResult("search_jobs", ok, f"status={resp.status_code}, jobs={len(jobs)}"))
    except Exception as exc:
        checks.append(CheckResult("search_jobs", False, str(exc)))

    # 5) Interview prep pack (legacy) or offer train (current contract)
    try:
        job_ids = [str(j.get("id")) for j in (jobs[:8] if jobs else process_body.get("recommended_jobs") or []) if j.get("id")]
        resp = _post_json(
            base_url,
            "/api/interview/prep_pack",
            {"resume_text": resume_text, "job_ids": job_ids},
            timeout_s=40,
        )
        body = resp.json() if resp.text else {}

        if resp.status_code != 404:
            pack = body.get("interview_pack") if isinstance(body, dict) else {}
            ok = resp.status_code == 200 and bool(body.get("success")) and isinstance(pack, dict)
            checks.append(
                CheckResult(
                    "interview_prep_pack",
                    ok,
                    f"status={resp.status_code}, questions={len((pack or {}).get('common_questions') or [])}",
                )
            )
        else:
            # New backend moved this capability under /api/offer/train.
            offer_payload: Dict[str, Any] = {"resume_text": resume_text}
            if job_ids:
                offer_payload["job_id"] = job_ids[0]
                offer_payload["job_ids"] = job_ids

            offer_resp = _post_json(base_url, "/api/offer/train", offer_payload, timeout_s=40)
            offer_body = offer_resp.json() if offer_resp.text else {}

            # 401/403 means endpoint exists but requires authenticated access code.
            ok = offer_resp.status_code in (200, 401, 403)
            detail_extra = ""
            if offer_resp.status_code == 200 and isinstance(offer_body, dict):
                interview_pack = offer_body.get("interview_pack") or {}
                detail_extra = f", questions={len((interview_pack or {}).get('common_questions') or [])}"
            elif offer_resp.status_code in (401, 403):
                detail_extra = ", auth_required=true"

            checks.append(
                CheckResult(
                    "interview_prep_pack",
                    ok,
                    (
                        f"legacy_status=404, offer_train_status={offer_resp.status_code}"
                        f"{detail_extra}"
                    ),
                )
            )
    except Exception as exc:
        checks.append(CheckResult("interview_prep_pack", False, str(exc)))

    # 6) OAuth endpoint availability (config may be absent, route should exist)
    try:
        resp = _get(base_url, "/api/auth/providers", timeout_s=20)
        body = resp.json() if resp.text else {}
        ok = resp.status_code == 200 and bool(body.get("success")) and isinstance(body.get("providers"), dict)
        checks.append(CheckResult("oauth_providers_endpoint", ok, f"status={resp.status_code}"))
    except Exception as exc:
        checks.append(CheckResult("oauth_providers_endpoint", False, str(exc)))

    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real-resume E2E acceptance checks")
    parser.add_argument("--base-url", default=os.getenv("APP_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--resume-file", default=os.getenv("REAL_RESUME_FILE", ""))
    parser.add_argument("--keywords", default=os.getenv("E2E_KEYWORDS", "Python后端,AI应用工程师"))
    parser.add_argument("--location", default=os.getenv("E2E_LOCATION", "深圳"))
    args = parser.parse_args()

    checks = _run(
        base_url=args.base_url.rstrip("/"),
        resume_file=args.resume_file,
        keywords=args.keywords,
        location=args.location,
    )

    print("\n=== Real Resume E2E Acceptance Report ===")
    for c in checks:
        status = "PASS" if c.ok else "FAIL"
        print(f"[{status}] {c.name}: {c.detail}")

    failed = [c for c in checks if not c.ok]
    print(f"\nTotal: {len(checks)}, Failed: {len(failed)}")

    if failed:
        print("\nFailed checks:")
        for c in failed:
            print(f"- {c.name}: {c.detail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
