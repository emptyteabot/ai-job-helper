#!/usr/bin/env python3
"""Strict smoke/e2e acceptance harness for ai-job-applier-web."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

try:
    import requests
    from requests import Session
    from requests.exceptions import RequestException
except ImportError as exc:
    print("requests is required for acceptance.py (pip install requests)", file=sys.stderr)
    raise SystemExit(1) from exc

PASS = "PASS"
ASSISTED = "ASSISTED"
FALLBACK = "FALLBACK"
FAIL = "FAIL"
DEFAULT_CODE = "123456"

STATUS_PRIORITY: Dict[str, int] = {
    PASS: 0,
    ASSISTED: 1,
    FALLBACK: 2,
    FAIL: 3,
}

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
        data = payload.get(section)
        if isinstance(data, dict):
            local_account = data.get("local_account")
            if isinstance(local_account, dict):
                return local_account
    return None


def probe_local_account_availability(session: Session, base_url: str) -> Dict[str, Any]:
    for endpoint in READINESS_ENDPOINTS:
        try:
            payload = request_json(session, "GET", endpoint, base_url)
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


class Reporter:
    def __init__(self) -> None:
        self.records: List[Dict[str, str]] = []
        self.status_report: Path | None = None

    def set_status_report(self, path: Path) -> None:
        self.status_report = path

    def status_counts(self) -> Counter[str]:
        return Counter(entry["status"] for entry in self.records)

    def overall_status(self) -> str:
        if not self.records:
            return PASS
        worst = max(self.records, key=lambda entry: STATUS_PRIORITY.get(entry["status"], 0))
        return worst["status"]

    def record(self, status: str, label: str, detail: str = "") -> None:
        stripped = detail or "OK"
        print(f"[{status}] {label} - {stripped}")
        self.records.append({"status": status, "label": label, "detail": stripped})

    def has_failures(self) -> bool:
        return any(entry["status"] == FAIL for entry in self.records)

    def summary(self) -> None:
        if not self.records:
            print("No steps executed.")
            self.write_status_report()
            return
        counts = Counter(entry["status"] for entry in self.records)
        print("\nSUMMARY")
        for status in (PASS, ASSISTED, FALLBACK, FAIL):
            if counts.get(status):
                print(f"  {status}: {counts[status]}")
        overall = self.overall_status()
        print(f"Overall status: {overall}")
        self.write_status_report()

    def write_status_report(self) -> None:
        if not self.status_report:
            return
        payload = {
            "overall_status": self.overall_status(),
            "counts": dict(self.status_counts()),
            "records": list(self.records),
        }
        self.status_report.parent.mkdir(parents=True, exist_ok=True)
        self.status_report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_success(payload: Dict[str, Any], label: str) -> None:
    success = payload.get("success")
    if success is False:
        raise RuntimeError(f"{label} returned success=false payload={json.dumps(payload, ensure_ascii=False)}")


def request_json(
    session: Session,
    method: str,
    endpoint: str,
    base_url: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}{endpoint}"
    timeout = kwargs.pop("timeout", getattr(session, "default_timeout", None))
    try:
        response = session.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
    except RequestException as exc:
        raise RuntimeError(f"{endpoint} failed ({exc})") from exc
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"{endpoint} returned invalid JSON ({exc})") from exc


def login_local_account(
    session: Session,
    base_url: str,
    email: str,
    password: str,
    register_if_missing: bool,
) -> Dict[str, Any]:
    try:
        payload = request_json(
            session,
            "POST",
            "/api/auth/local-login",
            base_url,
            json={"email": email, "password": password},
        )
    except RuntimeError as exc:
        if not register_if_missing or ("404" not in str(exc) and "401" not in str(exc)):
            raise
        payload = request_json(
            session,
            "POST",
            "/api/auth/local-register",
            base_url,
            json={"email": email, "password": password},
        )
    ensure_success(payload, "auth login")
    return payload


def fatal(reporter: Reporter, label: str, detail: str) -> None:
    reporter.record(FAIL, label, detail)
    raise SystemExit(1)


def is_live_job(job: Dict[str, Any]) -> bool:
    provider = str(job.get("provider") or "").strip()
    link = str(job.get("link") or job.get("url") or "").strip()
    if not link:
        return False
    if provider.startswith("fallback"):
        return False
    return True


def run_auth_flow(
    session: Session,
    reporter: Reporter,
    base_url: str,
    email: str,
    password: str,
    token_override: str | None,
    local_account_available: bool,
    readiness_endpoint: str | None,
) -> str:
    if token_override:
        status = ASSISTED if not local_account_available else PASS
        detail = "token override provided"
        if readiness_endpoint:
            detail += f" (auth readiness={readiness_endpoint})"
        reporter.record(status, "auth token override", detail)
        return token_override
    if not local_account_available:
        fatal(
            reporter,
            "auth readiness",
            "local_account login disabled and no --token supplied; aborting",
        )
    login = login_local_account(session, base_url, email, password, register_if_missing=True)
    token = login.get("token")
    if not token:
        fatal(reporter, "auth login", "response missing token")
    user = login.get("user", {})
    login_mode = login.get("auth_mode") or "local_account"
    login_env = login.get("auth_env") or "unknown"
    reporter.record(
        PASS,
        "auth login",
        f"id={user.get('id','unknown')} email={user.get('email','')} plan={user.get('plan')} remaining_quota={user.get('remaining_quota')} mode={login_mode} env={login_env}",
    )
    return token


def run_change_password_flow(
    session: Session,
    reporter: Reporter,
    base_url: str,
    email: str,
    password: str,
    token: str,
) -> str:
    next_password = _rotated_password(password)
    headers = {"Authorization": f"Bearer {token}"}

    try:
        changed = request_json(
            session,
            "POST",
            CHANGE_PASSWORD_ENDPOINT,
            base_url,
            headers=headers,
            json={"current_password": password, "new_password": next_password},
        )
        ensure_success(changed, "auth change-password")
    except Exception as exc:
        fatal(reporter, "auth change-password", str(exc))
    reporter.record(PASS, "auth change-password", "password updated")

    try:
        relogin = login_local_account(session, base_url, email, next_password, register_if_missing=False)
    except Exception as exc:
        fatal(reporter, "auth login after password change", str(exc))
    next_token = relogin.get("token")
    if not next_token:
        fatal(reporter, "auth login after password change", "response missing token")
    reporter.record(PASS, "auth login after password change", f"email={email}")

    try:
        restored = request_json(
            session,
            "POST",
            CHANGE_PASSWORD_ENDPOINT,
            base_url,
            headers={"Authorization": f"Bearer {next_token}"},
            json={"current_password": next_password, "new_password": password},
        )
        ensure_success(restored, "auth restore-password")
    except Exception as exc:
        fatal(reporter, "auth restore-password", str(exc))
    reporter.record(PASS, "auth restore-password", "password restored")

    try:
        restored_login = login_local_account(session, base_url, email, password, register_if_missing=False)
    except Exception as exc:
        fatal(reporter, "auth login after restore", str(exc))
    restored_token = restored_login.get("token")
    if not restored_token:
        fatal(reporter, "auth login after restore", "response missing token")
    reporter.record(PASS, "auth login after restore", f"email={email}")
    return restored_token


def run_resume_flow(
    session: Session,
    reporter: Reporter,
    base_url: str,
    token: str,
    resume_file: Path,
) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    with resume_file.open("rb") as fh:
        files = {"file": (resume_file.name, fh, "text/plain")}
        upload = request_json(session, "POST", "/api/resume/upload", base_url, headers=headers, files=files)
    ensure_success(upload, "resume upload")
    filename = upload.get("filename")
    if not filename:
        fatal(reporter, "resume upload", "missing filename in payload")
    reporter.record(PASS, "resume upload", f"{filename} ({resume_file.stat().st_size} bytes)")

    listing = request_json(session, "GET", "/api/resume/list", base_url, headers=headers)
    ensure_success(listing, "resume list")
    resumes = listing.get("resumes", [])
    if not resumes:
        fatal(reporter, "resume list", "returned empty list")
    if not any(entry.get("filename") == filename for entry in resumes):
        fatal(reporter, "resume list", f"{filename} missing from stored resumes")
    reporter.record(PASS, "resume list", f"{len(resumes)} entries found")

    text_response = request_json(session, "GET", f"/api/resume/text/{filename}", base_url, headers=headers)
    ensure_success(text_response, "resume text")
    text_body = text_response.get("text", "")
    if not text_body:
        fatal(reporter, "resume text", "empty resume text returned")
    reporter.record(PASS, "resume text", f"length={len(text_body.splitlines())} lines")


def run_hr_flow(
    session: Session,
    reporter: Reporter,
    base_url: str,
    hr_id: str,
    title: str,
    company: str,
    location: str,
    skills: List[str],
    min_years: int,
    max_candidates: int,
) -> str:
    job_payload = {
        "hr_id": hr_id,
        "title": title,
        "company": company,
        "location": location,
        "skills": skills,
        "min_years": min_years,
    }
    job_resp = request_json(session, "POST", "/api/hr/jobs", base_url, json=job_payload)
    ensure_success(job_resp, "HR job create")
    job = job_resp.get("job", {})
    job_id = job.get("job_id") or job.get("id")
    if not job_id:
        fatal(reporter, "HR job create", "missing job_id")
    reporter.record(PASS, "HR job create", f"id={job_id} title={job.get('title')}")

    overview = request_json(session, "GET", "/api/hr/overview", base_url, params={"hr_id": hr_id})
    ensure_success(overview, "HR overview")
    reporter.record(
        PASS,
        "HR overview",
        f"jobs={overview.get('jobs_count')} open={overview.get('open_jobs')} candidates={overview.get('candidates_count')}",
    )

    match = request_json(
        session,
        "GET",
        "/api/hr/candidates/match",
        base_url,
        params={"job_id": job_id, "hr_id": hr_id, "limit": max_candidates},
    )
    ensure_success(match, "HR candidate match")
    candidates = match.get("candidates", [])
    if not candidates:
        fatal(reporter, "HR candidate match", "no candidates returned")
    top = candidates[0]
    reporter.record(
        PASS,
        "HR candidate match",
        f"top={top.get('candidate_id')} score={top.get('score')} matched_skills={len(top.get('matched_skills', []))}",
    )
    return job_id


def run_jobs_flow(
    session: Session,
    reporter: Reporter,
    base_url: str,
    keyword: str,
    city: str,
    max_count: int,
) -> None:
    search = request_json(
        session,
        "GET",
        "/api/jobs/search",
        base_url,
        params={"keyword": keyword, "city": city, "max_count": max_count},
    )
    ensure_success(search, "jobs/search")
    jobs = search.get("jobs") or []
    if not jobs:
        fatal(reporter, "jobs/search", "returned zero jobs (jobs=0 is not a pass)")
    provider = str(search.get("provider") or "")
    provider_lower = provider.lower()
    warning = search.get("warning") or "<none>"
    has_live_jobs = any(is_live_job(job) for job in jobs)
    status = PASS
    if provider_lower == "openclaw_challenge":
        status = ASSISTED
    elif (provider_lower.startswith("fallback") and "legacy" not in provider_lower) or not has_live_jobs:
        status = FALLBACK
    elif provider_lower.startswith("legacy"):
        status = PASS
    elif provider in {"", "<missing>"}:
        status = FALLBACK
    reporter.record(
        status,
        "jobs/search",
        f"provider={provider or '<missing>'} live_jobs={has_live_jobs} warning={warning} total={len(jobs)} sample={jobs[0].get('title') or jobs[0].get('company') or '<unnamed>'}",
    )


def run_boss_flow(session: Session, reporter: Reporter, base_url: str) -> None:
    status = request_json(session, "GET", "/api/boss/status", base_url)
    ensure_success(status, "boss/status")
    tag = ASSISTED if status.get("assisted_only") else PASS
    detail = (
        f"available={status.get('available')} assisted_only={status.get('assisted_only')} "
        f"logged_in={status.get('logged_in')} message={status.get('message')}"
    )
    reporter.record(tag, "boss/status", detail)


def prepare_resume(resume_file: Path) -> None:
    default_text = "\n".join(
        [
            "John Doe",
            "Senior Backend Engineer",
            "Experience: 5+ years delivering Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, and LangChain-backed automation.",
            "Contributed to scalable REST APIs, GraphQL endpoints, and observability tooling.",
            "Projects: microservice mesh, event-driven ETL, and real-time dashboards.",
            "Skills: Python, FastAPI, Django, React, TypeScript, Node.js, Docker, Kubernetes, PostgreSQL, Redis, LangChain.",
            "Education: B.S. Computer Science",
        ]
    )
    resume_file.parent.mkdir(parents=True, exist_ok=True)
    if not resume_file.exists():
        resume_file.write_text(default_text + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rigorous acceptance harness for ai-job-applier-web")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765", help="Backend URL (must include http://)")
    parser.add_argument("--email", default=None, help="Email used for local account login/register")
    parser.add_argument("--password", default="Acceptance123!", help="Password used for local account login/register")
    parser.add_argument("--resume-file", default="scripts/sample_resume.txt", help="Resume file used for upload")
    parser.add_argument("--keyword", default="Python automation", help="jobs/search keyword")
    parser.add_argument("--city", default="Shanghai", help="jobs/search city")
    parser.add_argument("--max-jobs", type=int, default=8, help="jobs/search max_count")
    parser.add_argument("--hr-id", default="acceptance-hr", help="HR identifier")
    parser.add_argument("--job-title", default="Acceptance Automation Engineer", help="HR job title")
    parser.add_argument("--company", default="AgentHelpJob", help="HR job company")
    parser.add_argument("--location", default="Shanghai", help="HR job location")
    parser.add_argument("--skills", nargs="+", default=["Python", "FastAPI", "Automation"], help="HR job skills")
    parser.add_argument("--min-years", type=int, default=3, help="minimum years requested for HR job")
    parser.add_argument("--max-candidates", type=int, default=5, help="HR candidate match limit")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout seconds")
    parser.add_argument(
        "--status-report",
        default="scripts/.status/acceptance.json",
        help="File where per-step status counts and overall verdict are written",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Bearer token used for protected APIs (skips local account login). Required if local_account is disabled.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.email:
        args.email = f"acceptance-{int(time.time())}@agenthelpjob.com"
    reporter = Reporter()
    base_dir = Path(__file__).resolve().parent
    repo_root = base_dir.parent
    status_report_path = Path(args.status_report)
    if not status_report_path.is_absolute():
        status_report_path = repo_root / status_report_path
    reporter.set_status_report(status_report_path)
    resume_path = Path(args.resume_file)
    if not resume_path.is_absolute():
        resume_path = base_dir / resume_path.name
    prepare_resume(resume_path)
    session = requests.Session()
    session.default_timeout = args.timeout
    try:
        readiness = probe_local_account_availability(session, args.base_url)
        endpoint = readiness.get("endpoint") or "<unknown>"
        readiness_status = PASS if readiness.get("available") else ASSISTED
        detail_payload = readiness.get("detail")
        mode_label = "<unknown>"
        if isinstance(detail_payload, dict):
            mode_label = detail_payload.get("mode") or mode_label
        reporter.record(
            readiness_status,
            "auth readiness",
            f"endpoint={endpoint} local_account_enabled={readiness.get('available')} mode={mode_label}",
        )
        token_override = _normalize_token(args.token)
        token = run_auth_flow(
            session,
            reporter,
            args.base_url,
            args.email,
            args.password,
            token_override,
            readiness.get("available", True),
            readiness.get("endpoint"),
        )
        if not token_override:
            token = run_change_password_flow(session, reporter, args.base_url, args.email, args.password, token)
        run_resume_flow(session, reporter, args.base_url, token, resume_path)
        run_hr_flow(
            session,
            reporter,
            args.base_url,
            args.hr_id,
            args.job_title,
            args.company,
            args.location,
            args.skills,
            args.min_years,
            args.max_candidates,
        )
        run_jobs_flow(session, reporter, args.base_url, args.keyword, args.city, args.max_jobs)
        run_boss_flow(session, reporter, args.base_url)
    except SystemExit:
        raise
    except Exception as exc:
        fatal(reporter, "unexpected", str(exc))
    finally:
        session.close()
        reporter.summary()
        if reporter.has_failures():
            raise SystemExit(1)


if __name__ == "__main__":
    main()
