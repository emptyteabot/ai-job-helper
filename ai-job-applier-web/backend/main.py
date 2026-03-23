from __future__ import annotations

import asyncio
import base64
import hashlib
import html as html_lib
import hmac
import json
import os
import random
import re
import threading
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request as UrlRequest, urlopen

import PyPDF2
import docx
from fastapi import Body, Depends, FastAPI, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from pydantic import BaseModel

from boss_bridge import BossBridge
from challenge_center import ChallengeCenter
from hr_store import HRStore
from real_jobs_bridge import RealJobsBridge, _load_openclaw_provider, service_is_available
from sms_provider import resolve_sms_provider


app = FastAPI(title="AgentHelpJob Web Backend", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("APP_DATA_DIR", PROJECT_ROOT / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
AUTH_STORE_FILE = DATA_DIR / "auth_store.json"
HR_STORE_FILE = DATA_DIR / "hr_market.json"
RECORDS_STORE_FILE = DATA_DIR / "application_records.json"
CHALLENGE_STORE_FILE = DATA_DIR / "challenge_sessions.json"
CHALLENGE_SNAPSHOT_DIR = DATA_DIR / "challenge_snapshots"
BOSS_COOKIES_FILE = DATA_DIR / "boss_cookies.json"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

if (FRONTEND_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="frontend-assets")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
CODE_TTL_SECONDS = int(os.getenv("AUTH_CODE_TTL_SECONDS", "600"))

_raw_debug_code = os.getenv("AUTH_EXPOSE_DEBUG_CODE")
if _raw_debug_code is None or not str(_raw_debug_code).strip():
    EXPOSE_DEBUG_CODE = APP_ENV != "production"
else:
    EXPOSE_DEBUG_CODE = str(_raw_debug_code).strip().lower() in {"1", "true", "yes", "on"}

AUTH_BYPASS_DEFAULT = "123456" if APP_ENV != "production" else ""
AUTH_BYPASS_CODE = os.getenv("AUTH_BYPASS_CODE", AUTH_BYPASS_DEFAULT).strip()
AUTH_SMS_PROVIDER_ENV = os.getenv("AUTH_SMS_PROVIDER", "")
DEFAULT_SMS_PROVIDER_KEY = "console" if APP_ENV != "production" else ""
sms_provider_key = (AUTH_SMS_PROVIDER_ENV or DEFAULT_SMS_PROVIDER_KEY).strip()
sms_provider = resolve_sms_provider(sms_provider_key)
EMAIL_DIRECT_AUTH_ENABLED = os.getenv("AUTH_EMAIL_DIRECT_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
LOCAL_ACCOUNT_AUTH_ENABLED = os.getenv("AUTH_LOCAL_ACCOUNT_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
EMAIL_DIRECT_IP_WINDOW_SECONDS = int(os.getenv("AUTH_EMAIL_DIRECT_IP_WINDOW_SECONDS", "900"))
EMAIL_DIRECT_IP_MAX_ATTEMPTS = int(os.getenv("AUTH_EMAIL_DIRECT_IP_MAX_ATTEMPTS", "12"))
EMAIL_DIRECT_EMAIL_WINDOW_SECONDS = int(os.getenv("AUTH_EMAIL_DIRECT_EMAIL_WINDOW_SECONDS", "900"))
EMAIL_DIRECT_EMAIL_MAX_ATTEMPTS = int(os.getenv("AUTH_EMAIL_DIRECT_EMAIL_MAX_ATTEMPTS", "6"))
EMAIL_DIRECT_SIGNUP_WINDOW_SECONDS = int(os.getenv("AUTH_EMAIL_DIRECT_SIGNUP_WINDOW_SECONDS", "86400"))
EMAIL_DIRECT_IP_MAX_NEW_USERS = int(os.getenv("AUTH_EMAIL_DIRECT_IP_MAX_NEW_USERS", "3"))
EMAIL_DIRECT_NEW_USER_QUOTA = int(os.getenv("AUTH_EMAIL_DIRECT_NEW_USER_QUOTA", "3"))
ALLOW_SELF_SERVE_UPGRADE = os.getenv("ALLOW_SELF_SERVE_UPGRADE", "1" if APP_ENV != "production" else "0").strip().lower() in {"1", "true", "yes", "on"}
APPLY_MAX_ACTIVE_SESSIONS_PER_IP = int(os.getenv("APPLY_MAX_ACTIVE_SESSIONS_PER_IP", "2"))


def _current_auth_mode() -> str:
    if LOCAL_ACCOUNT_AUTH_ENABLED:
        return "local_account"
    if EMAIL_DIRECT_AUTH_ENABLED:
        return "email_direct"
    if EXPOSE_DEBUG_CODE:
        return "debug_code"
    if sms_provider.configured:
        return "sms_code"
    return "strict_code"


def _sms_auth_mode() -> str:
    if EXPOSE_DEBUG_CODE:
        return "debug_code"
    if sms_provider.configured:
        return "sms_code"
    return "strict_code"


def _primary_auth_provider() -> str:
    if LOCAL_ACCOUNT_AUTH_ENABLED:
        return "local_account"
    if EMAIL_DIRECT_AUTH_ENABLED:
        return "email_direct"
    if sms_provider.configured or EXPOSE_DEBUG_CODE:
        return "sms_code"
    return "strict_code"


AUTH_MODE = _current_auth_mode()


def _auth_mode_info() -> Dict[str, Any]:
    return {
        "mode": _current_auth_mode(),
        "env": APP_ENV,
        "debug_code_exposed": EXPOSE_DEBUG_CODE,
        "bypass_code_configured": EXPOSE_DEBUG_CODE and bool(AUTH_BYPASS_CODE),
        "production_mode": APP_ENV == "production",
    }

ALLOW_SIMULATED_APPLY = os.getenv(
    "ALLOW_SIMULATED_APPLY",
    "1",
).strip().lower() in {"1", "true", "yes", "on"}

llm_client = (
    AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    if DEEPSEEK_API_KEY
    else None
)

security = HTTPBearer(auto_error=False)
storage_lock = threading.RLock()
active_connections = defaultdict(list)
email_login_attempts_by_ip: Dict[str, List[float]] = defaultdict(list)
email_login_attempts_by_email: Dict[str, List[float]] = defaultdict(list)
email_signup_attempts_by_ip: Dict[str, List[float]] = defaultdict(list)
active_apply_users: set[str] = set()
active_apply_ips: Dict[str, int] = defaultdict(int)
hr_store = HRStore(HR_STORE_FILE)
jobs_bridge = RealJobsBridge()
boss_bridge = BossBridge()
challenge_center = ChallengeCenter(CHALLENGE_STORE_FILE, CHALLENGE_SNAPSHOT_DIR)
cached_jobs_by_id: Dict[str, Dict[str, Any]] = {}


class User(BaseModel):
    id: str
    phone: str = ""
    email: Optional[str] = None
    nickname: str = "user"
    plan: str = "free"
    remaining_quota: int = 5
    created_at: datetime
    expired_at: Optional[datetime] = None


class RegisterRequest(BaseModel):
    phone: str
    code: str
    nickname: Optional[str] = "user"


class LoginRequest(BaseModel):
    phone: str
    code: str


class EmailLoginRequest(BaseModel):
    email: str
    nickname: Optional[str] = None


class LocalRegisterRequest(BaseModel):
    email: str
    password: str
    nickname: Optional[str] = None


class LocalLoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str


class UpgradeRequest(BaseModel):
    plan: str


class ChallengeStartRequest(BaseModel):
    url: str
    title: Optional[str] = None
    provider: str = "playwright"


class ChallengeSubmitRequest(BaseModel):
    code: str


class ChallengeClickRequest(BaseModel):
    x: float
    y: float
    image_width: float
    image_height: float


class ChallengeDragRequest(BaseModel):
    from_x: float
    from_y: float
    to_x: float
    to_y: float
    image_width: float
    image_height: float
    steps: int = 18


class ChallengeAutofillRequest(BaseModel):
    overrides: Dict[str, Any] = {}


class HRJobRequest(BaseModel):
    hr_id: str
    title: str
    company: str
    location: str = ""
    skills: List[str] = []
    min_years: int = 0


class HRActionRequest(BaseModel):
    candidate_id: str
    job_id: str
    action: str
    hr_id: str = ""


class ResumeAnalysisRequest(BaseModel):
    resume_text: str
    analysis_type: str = "full"


class OpenClawSearchRequest(BaseModel):
    keywords: str
    location: str = "全国"
    experience: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    limit: int = 50


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_model_dump(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return json.loads(model.json())


def _serialize_user(user: User) -> Dict[str, Any]:
    return _safe_model_dump(user)


def _deserialize_user(data: Dict[str, Any]) -> User:
    payload = dict(data or {})
    created_at = payload.get("created_at")
    expired_at = payload.get("expired_at")
    def _parse_dt(value: Any):
        if not isinstance(value, str) or not value:
            return value
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    if isinstance(created_at, str):
        payload["created_at"] = _parse_dt(created_at)
    if isinstance(expired_at, str) and expired_at:
        payload["expired_at"] = _parse_dt(expired_at)
    return User(**payload)


def _default_auth_store() -> Dict[str, Any]:
    return {"users": {}, "codes": {}, "tasks": {}, "credentials": {}, "records": []}


def _load_auth_store() -> Dict[str, Any]:
    if not AUTH_STORE_FILE.exists():
        return _default_auth_store()
    try:
        raw = json.loads(AUTH_STORE_FILE.read_text(encoding="utf-8") or "{}")
    except Exception:
        return _default_auth_store()

    store = _default_auth_store()
    users = raw.get("users", {})
    codes = raw.get("codes", {})
    tasks = raw.get("tasks", {})
    credentials = raw.get("credentials", {})
    records = raw.get("records", [])
    if isinstance(users, dict):
        store["users"] = users
    if isinstance(codes, dict):
        store["codes"] = codes
    if isinstance(tasks, dict):
        store["tasks"] = tasks
    if isinstance(credentials, dict):
        store["credentials"] = credentials
    if isinstance(records, list):
        store["records"] = records
    return store


def _save_auth_store() -> None:
    AUTH_STORE_FILE.write_text(
        json.dumps(
            {
                "users": {
                    user_id: _serialize_user(user)
                    for user_id, user in users_db.items()
                },
                "codes": verification_codes,
                "tasks": tasks_db,
                "credentials": credentials_db,
                "records": application_records_db,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


auth_store = _load_auth_store()
users_db: Dict[str, User] = {
    user_id: _deserialize_user(payload)
    for user_id, payload in auth_store.get("users", {}).items()
    if isinstance(payload, dict)
}
verification_codes: Dict[str, Dict[str, Any]] = {
    str(phone): dict(payload)
    for phone, payload in auth_store.get("codes", {}).items()
    if isinstance(payload, dict)
}
tasks_db: Dict[str, Dict[str, Any]] = {
    str(task_id): dict(payload)
    for task_id, payload in auth_store.get("tasks", {}).items()
    if isinstance(payload, dict)
}
credentials_db: Dict[str, Dict[str, Any]] = {
    str(user_id): dict(payload)
    for user_id, payload in auth_store.get("credentials", {}).items()
    if isinstance(payload, dict)
}


def _load_records_store() -> List[Dict[str, Any]]:
    if not RECORDS_STORE_FILE.exists():
        return []
    try:
        raw = json.loads(RECORDS_STORE_FILE.read_text(encoding="utf-8") or "[]")
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    return [dict(item) for item in raw if isinstance(item, dict)]


def _save_records_store() -> None:
    RECORDS_STORE_FILE.write_text(
        json.dumps(application_records_db, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


application_records_db: List[Dict[str, Any]] = _load_records_store()


def _persist_records_store() -> None:
    with storage_lock:
        _save_records_store()


def _persist_all() -> None:
    with storage_lock:
        _save_auth_store()


def _save_pending_task(task_id: str, payload: Dict[str, Any]) -> None:
    tasks_db[str(task_id)] = dict(payload)
    _persist_all()


def _get_pending_task(task_id: str) -> Dict[str, Any]:
    return dict(tasks_db.get(str(task_id or ""), {}))


def _delete_pending_task(task_id: str) -> None:
    tasks_db.pop(str(task_id or ""), None)
    _persist_all()


def _record_application(
    user_id: str,
    *,
    job_title: str,
    company: str,
    status: str,
    source: str = "",
    url: str = "",
    detail: str = "",
    job_id: str = "",
    mode: str = "web",
    ) -> Dict[str, Any]:
    return _append_application_record(
        user_id=str(user_id or "").strip(),
        job_id=str(job_id or "").strip(),
        job_title=str(job_title or "").strip(),
        company=str(company or "").strip(),
        status=str(status or "pending").strip().lower(),
        source=str(source or mode or "").strip(),
        cover_letter=str(detail or "").strip(),
        response=str(url or "").strip(),
    )


def _is_direct_apply_target(job: Dict[str, Any]) -> bool:
    url = str(job.get("url") or job.get("link") or "").strip().lower()
    title = str(job.get("title") or job.get("job_title") or "").strip().lower()
    provider = str(job.get("provider") or "").strip().lower()
    if not url:
        return False
    if provider == "cn_portal":
        return False
    blocked_url_markers = (
        "zhipin.com/web/geek/job?query=",
        "sou.zhaopin.com",
        "liepin.com/zhaopin/",
        "job?query=",
    )
    blocked_title_markers = (
        "鎼滅储鍏ュ彛",
        "search entry",
    )
    if any(marker in url for marker in blocked_url_markers):
        return False
    if any(marker in title for marker in blocked_title_markers):
        return False
    return True


def _openclaw_runtime_status() -> Dict[str, Any]:
    return _openclaw_status_snapshot()


def _normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def _hash_password(password: str, salt_hex: Optional[str] = None) -> Dict[str, Any]:
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    iterations = 120000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return {
        "salt": salt.hex(),
        "iterations": iterations,
        "hash": derived.hex(),
        "algorithm": "pbkdf2_sha256",
    }


def _verify_password(stored: Dict[str, Any], password: str) -> bool:
    if not stored:
        return False
    algorithm = str(stored.get("algorithm") or "")
    if algorithm != "pbkdf2_sha256":
        return False
    try:
        salt_hex = str(stored.get("salt") or "")
        iterations = int(stored.get("iterations") or 120000)
        expected = str(stored.get("hash") or "")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iterations).hex()
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False


def _validate_password_strength(password: str) -> bool:
    return len(str(password or "")) >= 8


def _extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        candidate = forwarded.split(",", 1)[0].strip()
        try:
            return str(ip_address(candidate))
        except ValueError:
            pass
    if request.client and request.client.host:
        candidate = str(request.client.host).strip()
        try:
            return str(ip_address(candidate))
        except ValueError:
            return candidate or "unknown"
    return "unknown"


def _extract_websocket_ip(websocket: WebSocket) -> str:
    forwarded = websocket.headers.get("x-forwarded-for", "")
    if forwarded:
        candidate = forwarded.split(",", 1)[0].strip()
        try:
            return str(ip_address(candidate))
        except ValueError:
            pass
    candidate = (websocket.client.host if websocket.client else "") or ""
    if candidate:
        try:
            return str(ip_address(candidate))
        except ValueError:
            return candidate
    return "unknown"


def _validate_email_address(email: str) -> bool:
    candidate = _normalize_email(email)
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", candidate))


def _get_user_by_phone(phone: str) -> Optional[User]:
    phone = str(phone or "").strip()
    for user in users_db.values():
        if user.phone == phone:
            return user
    return None


def _get_user_by_email(email: str) -> Optional[User]:
    candidate = _normalize_email(email)
    if not candidate:
        return None
    for user in users_db.values():
        if _normalize_email(user.email or "") == candidate:
            return user
    return None


def _get_credentials_by_user_id(user_id: str) -> Dict[str, Any]:
    return dict(credentials_db.get(str(user_id or ""), {}))


def _prune_attempts(events: List[float], *, now_ts: float, window_seconds: int) -> List[float]:
    cutoff = now_ts - max(1, window_seconds)
    return [event for event in events if event >= cutoff]


def _check_and_record_limit(
    bucket: Dict[str, List[float]],
    key: str,
    *,
    window_seconds: int,
    max_events: int,
    now_ts: float,
) -> bool:
    existing = _prune_attempts(bucket.get(key, []), now_ts=now_ts, window_seconds=window_seconds)
    if len(existing) >= max_events:
        bucket[key] = existing
        return False
    existing.append(now_ts)
    bucket[key] = existing
    return True


def _enforce_email_direct_limits(request: Request, email: str, *, is_new_user: bool) -> None:
    client_ip = _extract_client_ip(request)
    now_ts = _utc_now().timestamp()
    with storage_lock:
        if not _check_and_record_limit(
            email_login_attempts_by_ip,
            client_ip,
            window_seconds=EMAIL_DIRECT_IP_WINDOW_SECONDS,
            max_events=max(1, EMAIL_DIRECT_IP_MAX_ATTEMPTS),
            now_ts=now_ts,
        ):
            raise HTTPException(status_code=429, detail="too many email login attempts from this IP, try again later")

        if not _check_and_record_limit(
            email_login_attempts_by_email,
            email,
            window_seconds=EMAIL_DIRECT_EMAIL_WINDOW_SECONDS,
            max_events=max(1, EMAIL_DIRECT_EMAIL_MAX_ATTEMPTS),
            now_ts=now_ts,
        ):
            raise HTTPException(status_code=429, detail="too many login attempts for this email, try again later")

        if is_new_user and not _check_and_record_limit(
            email_signup_attempts_by_ip,
            client_ip,
            window_seconds=EMAIL_DIRECT_SIGNUP_WINDOW_SECONDS,
            max_events=max(1, EMAIL_DIRECT_IP_MAX_NEW_USERS),
            now_ts=now_ts,
        ):
            raise HTTPException(status_code=429, detail="too many new accounts created from this IP, try again later")


def _acquire_apply_slot(user_id: str, client_ip: str) -> None:
    normalized_ip = client_ip or "unknown"
    with storage_lock:
        if user_id in active_apply_users:
            raise HTTPException(status_code=409, detail="an apply session is already active for this account")
        current_ip_count = active_apply_ips.get(normalized_ip, 0)
        if current_ip_count >= max(1, APPLY_MAX_ACTIVE_SESSIONS_PER_IP):
            raise HTTPException(status_code=429, detail="too many active apply sessions from this IP")
        active_apply_users.add(user_id)
        active_apply_ips[normalized_ip] = current_ip_count + 1


def _release_apply_slot(user_id: str, client_ip: str) -> None:
    normalized_ip = client_ip or "unknown"
    with storage_lock:
        active_apply_users.discard(user_id)
        current_ip_count = active_apply_ips.get(normalized_ip, 0)
        if current_ip_count <= 1:
            active_apply_ips.pop(normalized_ip, None)
        else:
            active_apply_ips[normalized_ip] = current_ip_count - 1


def _generate_verification_code() -> str:
    if EXPOSE_DEBUG_CODE and AUTH_BYPASS_CODE:
        return AUTH_BYPASS_CODE
    return "".join(str(random.randint(0, 9)) for _ in range(6))


def _store_verification_code(phone: str, code: str) -> None:
    verification_codes[str(phone).strip()] = {
        "code": code,
        "expires_at": (_utc_now() + timedelta(seconds=CODE_TTL_SECONDS)).isoformat(),
    }
    _persist_all()


def _validate_verification_code(phone: str, code: str) -> bool:
    record = verification_codes.get(str(phone).strip())
    if not record:
        return False
    expires_at = record.get("expires_at")
    if not expires_at:
        return False
    try:
        if datetime.fromisoformat(expires_at) < _utc_now():
            verification_codes.pop(str(phone).strip(), None)
            _persist_all()
            return False
    except Exception:
        return False
    return str(record.get("code") or "").strip() == str(code or "").strip()


def _consume_verification_code(phone: str) -> None:
    verification_codes.pop(str(phone).strip(), None)
    _persist_all()


def _create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": int((_utc_now() + timedelta(days=30)).timestamp()),
    }
    body = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def _verify_token(token: str) -> Optional[str]:
    try:
        body, signature = str(token or "").split(".", 1)
        expected = hmac.new(SECRET_KEY.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padding = "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode((body + padding).encode("ascii")).decode("utf-8"))
        if int(payload.get("exp") or 0) < int(_utc_now().timestamp()):
            return None
    except Exception:
        return None
    return payload.get("user_id")


def _optional_user_from_token(token: str) -> Optional[User]:
    user_id = _verify_token(str(token or "").strip())
    if not user_id:
        return None
    return users_db.get(str(user_id))


def _extract_optional_user_from_request(request: Request) -> Optional[User]:
    auth_header = str(request.headers.get("authorization") or "").strip()
    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = str(request.query_params.get("token") or "").strip()
    return _optional_user_from_token(token)


def _extract_optional_user_from_websocket(websocket: WebSocket, data: Dict[str, Any]) -> Optional[User]:
    token = str((data or {}).get("token") or "").strip()
    if not token:
        auth_header = str(websocket.headers.get("authorization") or "").strip()
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = str(websocket.query_params.get("token") or "").strip()
    return _optional_user_from_token(token)


def _normalize_record_status(status: str) -> str:
    candidate = str(status or "").strip().lower()
    if candidate not in {"success", "failed", "pending"}:
        return "pending"
    return candidate


def _coerce_iso_timestamp(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        candidate = value.strip().replace("Z", "+00:00")
        try:
            datetime.fromisoformat(candidate)
            return candidate
        except Exception:
            pass
    return _utc_now().isoformat()


def _normalize_record_row(row: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(row or {})
    applied_at = _coerce_iso_timestamp(item.get("applied_at") or item.get("created_at"))
    item["id"] = str(item.get("id") or uuid.uuid4().hex)
    item["job_id"] = str(item.get("job_id") or item["id"])
    item["job_title"] = str(item.get("job_title") or item.get("title") or "")
    item["company"] = str(item.get("company") or "")
    item["salary"] = str(item.get("salary") or "")
    item["location"] = str(item.get("location") or "")
    item["status"] = _normalize_record_status(item.get("status") or "pending")
    item["cover_letter"] = str(item.get("cover_letter") or "")
    item["response"] = str(item.get("response") or "")
    item["source"] = str(item.get("source") or "")
    item["user_id"] = str(item.get("user_id") or "")
    item["applied_at"] = applied_at
    item["created_at"] = _coerce_iso_timestamp(item.get("created_at") or applied_at)
    return item


def _append_application_record(
    *,
    user_id: str = "",
    job_id: str = "",
    job_title: str = "",
    company: str = "",
    salary: str = "",
    location: str = "",
    status: str = "pending",
    cover_letter: str = "",
    response: str = "",
    source: str = "",
) -> Dict[str, Any]:
    entry = _normalize_record_row(
        {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "job_id": job_id,
            "job_title": job_title,
            "company": company,
            "salary": salary,
            "location": location,
            "status": status,
            "cover_letter": cover_letter,
            "response": response,
            "source": source,
        }
    )
    with storage_lock:
        application_records_db.append(entry)
        _save_records_store()
    return entry


def _list_application_records(
    *,
    status: str = "",
    limit: int = 100,
    offset: int = 0,
    user_id: str = "",
) -> Dict[str, Any]:
    with storage_lock:
        rows = [_normalize_record_row(row) for row in application_records_db]
    filtered = rows
    if user_id:
        filtered = [row for row in filtered if str(row.get("user_id") or "") == user_id]
    normalized_status = _normalize_record_status(status) if status else ""
    if normalized_status:
        filtered = [row for row in filtered if row.get("status") == normalized_status]
    filtered.sort(
        key=lambda row: (
            str(row.get("applied_at") or ""),
            str(row.get("created_at") or ""),
        ),
        reverse=True,
    )
    safe_offset = max(0, int(offset or 0))
    safe_limit = max(1, min(int(limit or 100), 1_000_000))
    return {
        "total": len(filtered),
        "records": filtered[safe_offset:safe_offset + safe_limit],
    }


def _application_record_stats(user_id: str = "") -> Dict[str, Any]:
    listing = _list_application_records(status="", limit=1_000_000, offset=0, user_id=user_id)
    records = listing["records"]
    total = len(records)
    success = sum(1 for row in records if row.get("status") == "success")
    failed = sum(1 for row in records if row.get("status") == "failed")
    pending = sum(1 for row in records if row.get("status") == "pending")
    success_rate = round((success / total) * 100, 2) if total else 0
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "pending": pending,
        "success_rate": success_rate,
    }


def _cache_jobs(rows: List[Dict[str, Any]]) -> None:
    with storage_lock:
        for row in rows:
            job_id = str(row.get("job_id") or row.get("id") or "").strip()
            if not job_id:
                continue
            cached_jobs_by_id[job_id] = dict(row)
        if len(cached_jobs_by_id) > 5000:
            overflow = len(cached_jobs_by_id) - 5000
            for key in list(cached_jobs_by_id.keys())[:overflow]:
                cached_jobs_by_id.pop(key, None)


def _job_from_cache(job_id: str) -> Dict[str, Any]:
    candidate = str(job_id or "").strip()
    if not candidate:
        return {}
    with storage_lock:
        row = dict(cached_jobs_by_id.get(candidate, {}))
    if row:
        row.setdefault("job_id", candidate)
        row.setdefault("id", candidate)
    return row


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="missing authorization")
    user_id = _verify_token(credentials.credentials)
    user = users_db.get(str(user_id or ""))
    if not user:
        raise HTTPException(status_code=401, detail="invalid token")
    return user


def _sanitize_filename(filename: str) -> str:
    safe = Path(str(filename or "resume")).name
    safe = re.sub(r"[^\w.\-() ]+", "_", safe)
    return safe or "resume"


def _candidate_payload_from_resume(user: User, resume_text: str, resume_filename: str) -> Dict[str, Any]:
    return {
        "candidate_id": user.id,
        "user_id": user.id,
        "phone": user.phone,
        "email": user.email or "",
        "nickname": user.nickname,
        "resume_text": resume_text,
        "resume_filename": resume_filename,
        "skills": _extract_skills(resume_text),
        "years_experience": _extract_years_experience(resume_text),
        "location": _extract_location(resume_text),
    }


def extract_text_from_pdf(file_path: str) -> str:
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text).strip()


def extract_text_from_docx(file_path: str) -> str:
    document = docx.Document(file_path)
    return "\n".join(para.text for para in document.paragraphs).strip()


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(str(file_path))
    if suffix == ".docx":
        return extract_text_from_docx(str(file_path))
    if suffix == ".doc":
        raise HTTPException(status_code=400, detail="legacy .doc is not supported, please convert it to .docx")
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore").strip()
    raise HTTPException(status_code=400, detail="unsupported file type")


def _extract_skills(text: str) -> List[str]:
    keywords = [
        "python", "java", "golang", "go", "javascript", "typescript",
        "react", "vue", "node.js", "fastapi", "django", "flask",
        "mysql", "postgresql", "redis", "docker", "kubernetes",
        "langchain", "rag", "llm", "pytorch", "tensorflow",
    ]
    lower_text = str(text or "").lower()
    return [keyword for keyword in keywords if keyword in lower_text]


def _extract_years_experience(text: str) -> int:
    years = [
        int(match.group(1))
        for match in re.finditer(r"(\d{1,2})\s*(?:\+)?\s*(?:years?|yrs?|\u5e74)", str(text or ""), re.I)
    ]
    if not years:
        return 0
    return max(0, min(max(years), 30))


def _extract_location(text: str) -> str:
    choices = ["beijing", "shanghai", "shenzhen", "hangzhou", "guangzhou", "chengdu", "北京", "上海", "深圳", "杭州", "广州", "成都"]
    lower_text = str(text or "").lower()
    for item in choices:
        if item.lower() in lower_text:
            return item
    return ""


def _extract_email_from_text(text: str) -> str:
    match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", str(text or ""), re.I)
    return str(match.group(0) or "").strip() if match else ""


def _extract_phone_from_text(text: str) -> str:
    candidates = re.findall(r"(?:\+?86[-\s]?)?(1[3-9]\d{9})", str(text or ""))
    return str(candidates[0] or "").strip() if candidates else ""


def _extract_url_from_text(text: str, keyword: str) -> str:
    for match in re.findall(r"https?://[^\s)>\"]+", str(text or ""), re.I):
        if keyword.lower() in match.lower():
            return str(match).strip()
    return ""


def _extract_school_from_text(text: str) -> str:
    school_keywords = ("大学", "学院", "university", "college", "institute")
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if len(line) > 80:
            continue
        if any(keyword.lower() in line.lower() for keyword in school_keywords):
            return line
    return ""


def _extract_degree_from_text(text: str) -> str:
    patterns = ("博士", "硕士", "本科", "专科", "phd", "master", "bachelor", "associate")
    lower_text = str(text or "").lower()
    for pattern in patterns:
        if pattern.lower() in lower_text:
            return pattern
    return ""


def _extract_major_from_text(text: str) -> str:
    match = re.search(r"(?:专业|major)[:：]?\s*([^\n,，|]{2,40})", str(text or ""), re.I)
    return str(match.group(1) or "").strip() if match else ""


def _extract_name_from_text(text: str) -> str:
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line or "@" in line or len(line) > 24:
            continue
        if re.search(r"\d", line):
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]{2,5}", line):
            return line
        if re.fullmatch(r"[A-Za-z]+(?:\s+[A-Za-z]+){0,2}", line):
            return line
    return ""


def _get_latest_resume_text_for_user(user: User) -> str:
    prefix = f"{user.id}__"
    candidates = sorted(UPLOAD_DIR.glob(f"{prefix}*"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return ""
    try:
        return extract_text_from_file(candidates[0])
    except Exception:
        return ""


def _build_autofill_profile(user: User, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    resume_text = _get_latest_resume_text_for_user(user)
    nickname = str(user.nickname or "").strip()
    full_name = nickname if nickname and nickname.lower() != "user" else _extract_name_from_text(resume_text)
    profile = {
        "full_name": full_name,
        "email": str(user.email or "").strip() or _extract_email_from_text(resume_text),
        "phone": str(user.phone or "").strip() or _extract_phone_from_text(resume_text),
        "location_city": _extract_location(resume_text),
        "school": _extract_school_from_text(resume_text),
        "degree": _extract_degree_from_text(resume_text),
        "major": _extract_major_from_text(resume_text),
        "github_url": _extract_url_from_text(resume_text, "github.com"),
        "linkedin_url": _extract_url_from_text(resume_text, "linkedin.com"),
        "portfolio_url": _extract_url_from_text(resume_text, ""),
        "summary": " ".join(line.strip() for line in resume_text.splitlines()[:6] if line.strip())[:600],
        "resume_text": resume_text[:4000],
    }
    for key, value in (overrides or {}).items():
        if value is None:
            continue
        profile[str(key)] = str(value).strip()
    return profile


def _normalize_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, (tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        if "," in value:
            return [part.strip() for part in value.split(",") if part.strip()]
        return [value.strip()]
    return []


def _to_legacy_openclaw_job(job: Dict[str, Any], fallback_location: str, index: int) -> Dict[str, Any]:
    job_id = str(job.get("job_id") or job.get("id") or f"job_{index}_{uuid.uuid4().hex[:8]}")
    return {
        "job_id": job_id,
        "id": job_id,
        "title": str(job.get("title") or ""),
        "job_title": str(job.get("job_title") or job.get("title") or ""),
        "company": str(job.get("company") or ""),
        "salary": str(job.get("salary") or ""),
        "location": str(job.get("location") or fallback_location or ""),
        "experience": str(job.get("experience") or ""),
        "education": str(job.get("education") or ""),
        "description": str(job.get("description") or ""),
        "skills": _normalize_string_list(job.get("skills") or job.get("requirements")),
        "welfare": _normalize_string_list(job.get("welfare")),
        "boss_name": str(job.get("boss_name") or ""),
        "boss_title": str(job.get("boss_title") or ""),
        "url": str(job.get("url") or job.get("link") or ""),
        "source": str(job.get("source") or job.get("provider") or ""),
        "provider": str(job.get("provider") or ""),
    }


def _openclaw_source(provider: str) -> str:
    normalized = str(provider or "").strip().lower()
    if normalized in {"openclaw", "openclaw_challenge"}:
        return "openclaw"
    if not normalized or normalized == "fallback" or normalized.startswith("fallback"):
        return "mock"
    return normalized


def _openclaw_status_snapshot() -> Dict[str, Any]:
    provider = _load_openclaw_provider()
    if provider is None:
        return {
            "available": False,
            "status": "error",
            "message": "OpenClaw provider unavailable",
        }
    try:
        health = provider.health_check()
    except Exception as exc:
        return {
            "available": False,
            "status": "error",
            "message": f"OpenClaw health check failed: {exc}",
        }
    available = bool((health or {}).get("available"))
    return {
        "available": available,
        "status": str((health or {}).get("status") or ("ready" if available else "error")),
        "message": str((health or {}).get("message") or ("OpenClaw available" if available else "OpenClaw unavailable")),
    }


def _resume_role_candidates(skills: List[str]) -> List[str]:
    skill_set = {item.lower() for item in skills}
    roles: List[str] = []
    if {"python", "fastapi", "django", "flask"} & skill_set:
        roles.append("Backend Engineer (Python)")
    if {"javascript", "typescript", "react", "vue"} & skill_set:
        roles.append("Frontend or Fullstack Engineer")
    if {"pytorch", "tensorflow", "llm", "rag"} & skill_set:
        roles.append("AI/ML Engineer")
    if {"docker", "kubernetes", "redis", "postgresql"} & skill_set:
        roles.append("Platform Engineer / DevOps")
    if not roles:
        roles = ["Software Engineer", "Implementation Engineer", "Data Analyst"]
    return roles[:3]


async def _build_resume_analysis_results(resume_text: str, analysis_type: str) -> Dict[str, Any]:
    text = str(resume_text or "").strip()
    if not text:
        return {}
    skills = _extract_skills(text)
    years = _extract_years_experience(text)
    location = _extract_location(text) or "unspecified"
    top_skills = ", ".join(skills[:8]) if skills else "no strong technical keywords detected"
    role_candidates = _resume_role_candidates(skills)

    career_analysis = (
        "Career profile summary:\n"
        f"- Experience: about {years} year(s)\n"
        f"- Preferred location: {location}\n"
        f"- Skills: {top_skills}\n\n"
        "Recommendation: start with high-match roles, then expand to adjacent roles after interview conversion stabilizes."
    )
    job_recommendations = (
        "Recommended role priorities:\n"
        + "\n".join(f"{index}. {role}" for index, role in enumerate(role_candidates, 1))
        + "\n\nApply strategy: prioritize core-fit jobs first, then add 1-2 stretch roles."
    )
    interview_preparation = (
        "Interview preparation checklist:\n"
        "1. Prepare 2-3 project stories with business goal, design choice, and measurable outcome.\n"
        "2. Explain one key architecture tradeoff clearly.\n"
        "3. Prepare one failure postmortem using STAR.\n"
        "4. Review system design and performance optimization basics for target roles."
    )
    skill_gap_analysis = (
        "Quality audit and skill-gap notes:\n"
        f"- Detected skills: {top_skills}\n"
        "- Potential gaps: weak quantified outcomes, limited collaboration evidence, and vague business impact wording.\n"
        "- Next step: rewrite each project as Goal -> Actions -> Results with explicit metrics."
    )

    mode = str(analysis_type or "full").strip().lower()
    results: Dict[str, Any] = {}
    if mode in {"full", "career"}:
        results["career_analysis"] = career_analysis
    if mode in {"full", "jobs"}:
        results["job_recommendations"] = job_recommendations
    if mode in {"full", "interview"}:
        results["interview_preparation"] = interview_preparation
        results["mock_interview"] = interview_preparation
    if mode in {"full", "quality"}:
        results["skill_gap_analysis"] = skill_gap_analysis
        results["quality_audit"] = skill_gap_analysis
    return results


def _http_get_text(url: str, timeout: int = 12) -> str:
    request = UrlRequest(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def _normalize_ddg_redirect(link: str) -> str:
    href = html_lib.unescape((link or "").strip())
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/l/?"):
        href = "https://duckduckgo.com" + href
    if "duckduckgo.com/l/?" in href:
        query = parse_qs(urlparse(href).query)
        uddg = query.get("uddg", [])
        if uddg:
            return uddg[0]
    return href


def _extract_company_from_title(title: str) -> str:
    parts = [part.strip() for part in re.split(r"[-|_璺痌", title) if part.strip()]
    if len(parts) >= 2:
        return parts[1]
    return ""


def _search_duckduckgo_jobs(keyword: str, city: str, limit: int) -> List[Dict[str, Any]]:
    query = quote_plus(f"{city} {keyword} site:zhipin.com/job_detail")
    html_text = _http_get_text(f"https://duckduckgo.com/html/?q={query}")
    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="(?P<link>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.I | re.S,
    )
    rows: List[Dict[str, Any]] = []
    for index, match in enumerate(pattern.finditer(html_text), 1):
        link = _normalize_ddg_redirect(match.group("link"))
        title = re.sub(r"<[^>]+>", " ", match.group("title"))
        title = html_lib.unescape(re.sub(r"\s+", " ", title)).strip()
        if not link or "zhipin.com" not in link:
            continue
        rows.append(
            {
                "id": f"ddg_{index}_{abs(hash(link))}",
                "title": title or f"{keyword} role",
                "company": _extract_company_from_title(title),
                "salary": "",
                "url": link,
                "source": "duckduckgo",
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _search_bing_jobs(keyword: str, city: str, limit: int) -> List[Dict[str, Any]]:
    query = quote_plus(f"{city} {keyword} site:zhipin.com/job_detail")
    html_text = _http_get_text(f"https://www.bing.com/search?q={query}")
    pattern = re.compile(
        r'<li class="b_algo"[^>]*>.*?<h2><a href="(?P<link>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.I | re.S,
    )
    rows: List[Dict[str, Any]] = []
    for index, match in enumerate(pattern.finditer(html_text), 1):
        link = html_lib.unescape((match.group("link") or "").strip())
        title = re.sub(r"<[^>]+>", " ", match.group("title"))
        title = html_lib.unescape(re.sub(r"\s+", " ", title)).strip()
        if not link or "zhipin.com" not in link:
            continue
        rows.append(
            {
                "id": f"bing_{index}_{abs(hash(link))}",
                "title": title or f"{keyword} role",
                "company": _extract_company_from_title(title),
                "salary": "",
                "url": link,
                "source": "bing",
            }
        )
        if len(rows) >= limit:
            break
    return rows


async def search_jobs(keyword: str, city: str, max_count: int) -> List[Dict[str, Any]]:
    loop = asyncio.get_running_loop()

    def _search() -> List[Dict[str, Any]]:
        result = jobs_bridge.search_jobs(keyword=keyword, city=city, limit=max_count)
        return result.jobs

    return await loop.run_in_executor(None, _search)


async def generate_greeting(job: Dict[str, Any], resume_text: str) -> str:
    if llm_client is None:
        title = job.get("title") or "this role"
        company = job.get("company") or "your company"
        return f"Hello, I am interested in {title} at {company}. My resume is a strong fit for the role."

    prompt = (
        "Write one concise job application opener under 60 words.\n\n"
        f"Job: {job.get('title', '')} - {job.get('company', '')}\n"
        f"Resume: {(resume_text or '')[:1000]}\n"
    )
    try:
        response = await llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=100,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception:
        return f"Hello, I am interested in {job.get('title', 'this role')} and would like to connect."


async def apply_single_job(job: Dict[str, Any], greeting: str) -> bool:
    # The current web backend still runs in assisted mode. Keep the delay realistic
    # so progress looks stable, but do not fake browser automation.
    await asyncio.sleep(1.2)
    if not ALLOW_SIMULATED_APPLY:
        return False
    return random.random() < 0.85


def _frontend_available() -> bool:
    return FRONTEND_INDEX_FILE.exists()


@app.get("/")
async def root():
    if _frontend_available():
        return FileResponse(FRONTEND_INDEX_FILE)
    return {"name": "AgentHelpJob Web Backend", "version": "2.1.0", "status": "running"}


@app.get("/health")
@app.get("/api/health")
async def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "env": APP_ENV,
        "users": len(users_db),
        "codes": len(verification_codes),
        "hr_jobs": len(hr_store.list_jobs(limit=10000)),
        "desktop_backend_url": jobs_bridge.desktop_backend_url,
        "boss_bridge_available": boss_bridge.available(),
    }


@app.get("/api/system/readiness")
async def system_readiness() -> Dict[str, Any]:
    openclaw_status = await asyncio.to_thread(_openclaw_status_snapshot)
    legacy_provider = jobs_bridge.last_live_provider()
    legacy_warning = ""
    if not legacy_provider:
        legacy_available, legacy_name, legacy_warning = await asyncio.to_thread(jobs_bridge.legacy_backend_health)
        if legacy_available:
            legacy_provider = legacy_name or "legacy_backend"
    if openclaw_status.get("available"):
        preferred_provider = "openclaw"
    elif service_is_available():
        preferred_provider = "desktop_real_job_service"
    elif legacy_provider:
        preferred_provider = legacy_provider
    else:
        preferred_provider = "fallback"
    jobs_warning = ""
    if preferred_provider == "fallback":
        jobs_warning = legacy_warning or "live provider currently unavailable"
    auth_meta = _auth_mode_info()
    return {
        "success": True,
        "frontend": {
            "available": _frontend_available(),
            "dist_dir": str(FRONTEND_DIST_DIR),
        },
        "auth": {
            "mode": auth_meta["mode"],
            "primary_provider": _primary_auth_provider(),
            "env": auth_meta["env"],
            "debug_code_exposed": auth_meta["debug_code_exposed"],
            "bypass_code_configured": auth_meta["bypass_code_configured"],
            "production_mode": auth_meta["production_mode"],
            "local_account": {
                "enabled": LOCAL_ACCOUNT_AUTH_ENABLED,
                "requires_password": True,
            },
            "email_direct": {
                "enabled": EMAIL_DIRECT_AUTH_ENABLED,
                "ip_window_seconds": EMAIL_DIRECT_IP_WINDOW_SECONDS,
                "ip_max_attempts": EMAIL_DIRECT_IP_MAX_ATTEMPTS,
                "email_window_seconds": EMAIL_DIRECT_EMAIL_WINDOW_SECONDS,
                "email_max_attempts": EMAIL_DIRECT_EMAIL_MAX_ATTEMPTS,
                "signup_window_seconds": EMAIL_DIRECT_SIGNUP_WINDOW_SECONDS,
                "ip_max_new_users": EMAIL_DIRECT_IP_MAX_NEW_USERS,
            },
            "persisted_users": len(users_db),
            "sms_provider": {
                "key": sms_provider.key,
                "configured": sms_provider.configured,
                "name": sms_provider.name,
                "help_text": sms_provider.help_text,
            },
        },
        "jobs": {
            "provider": preferred_provider,
            "warning": jobs_warning,
            "sample_count": None,
            "openclaw": openclaw_status,
        },
        "boss": {
            "available": boss_bridge.available(),
            "assisted_only": True,
            "status": boss_bridge.status(),
        },
        "hr": {
            "jobs_count": len(hr_store.list_jobs(limit=10000)),
            "candidate_count": len(hr_store.list_candidates(limit=10000)),
        },
    }


@app.get("/api/records")
async def list_records(
    request: Request,
    status: str = "",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    user = _extract_optional_user_from_request(request)
    listing = _list_application_records(
        status=status,
        limit=limit,
        offset=offset,
        user_id=(user.id if user else ""),
    )
    return {"success": True, "records": listing["records"], "total": listing["total"]}


@app.post("/api/records")
async def list_records_post(
    request: Request,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    user = _extract_optional_user_from_request(request)
    listing = _list_application_records(
        status=str(payload.get("status") or ""),
        limit=int(payload.get("limit") or 100),
        offset=int(payload.get("offset") or 0),
        user_id=(user.id if user else ""),
    )
    return {"success": True, "records": listing["records"], "total": listing["total"]}


@app.get("/api/records/stats")
async def records_stats(request: Request) -> Dict[str, Any]:
    user = _extract_optional_user_from_request(request)
    return _application_record_stats(user.id if user else "")


@app.post("/api/records/stats")
async def records_stats_post(request: Request) -> Dict[str, Any]:
    user = _extract_optional_user_from_request(request)
    return _application_record_stats(user.id if user else "")


@app.get("/api/openclaw/status")
async def openclaw_status() -> Dict[str, Any]:
    status = await asyncio.to_thread(_openclaw_status_snapshot)
    return {
        "available": bool(status.get("available")),
        "status": str(status.get("status") or ""),
        "message": str(status.get("message") or ""),
    }


async def _run_openclaw_search(
    *,
    keywords: str,
    location: str,
    salary_min: int,
    limit: int,
) -> Dict[str, Any]:
    search_result = await asyncio.to_thread(jobs_bridge.search_jobs, keywords, location, limit)
    jobs = [
        _to_legacy_openclaw_job(job, location, index)
        for index, job in enumerate(search_result.jobs, 1)
    ]
    if salary_min > 0:
        filtered: List[Dict[str, Any]] = []
        for job in jobs:
            salary_text = str(job.get("salary") or "")
            numbers = [int(item) for item in re.findall(r"\d+", salary_text)]
            if not numbers or max(numbers) >= salary_min:
                filtered.append(job)
        jobs = filtered
    _cache_jobs(jobs)
    source = _openclaw_source(search_result.provider)
    message = search_result.warning or f"found {len(jobs)} jobs"
    return {
        "success": True,
        "jobs": jobs,
        "total": len(jobs),
        "source": source,
        "provider": search_result.provider,
        "warning": search_result.warning,
        "message": message,
    }


@app.get("/api/openclaw/search")
async def openclaw_search(
    keywords: str = Query(..., min_length=1),
    location: str = Query("全国"),
    salary_min: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    return await _run_openclaw_search(
        keywords=keywords,
        location=location,
        salary_min=salary_min,
        limit=limit,
    )


@app.post("/api/openclaw/search")
async def openclaw_search_post(req: OpenClawSearchRequest) -> Dict[str, Any]:
    return await _run_openclaw_search(
        keywords=req.keywords,
        location=req.location or "全国",
        salary_min=max(0, int(req.salary_min or 0)),
        limit=max(1, min(int(req.limit or 50), 200)),
    )




@app.get("/api/challenges")
async def list_challenges(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    sessions = challenge_center.list_sessions(user_id=user.id)
    return {"success": True, "sessions": sessions}


@app.post("/api/challenges/start")
async def start_challenge(req: ChallengeStartRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    session = await challenge_center.start_session(
        user_id=user.id,
        url=req.url,
        title=req.title or "Challenge Session",
        provider=req.provider or "playwright",
    )
    return {"success": True, "session": session}


@app.get("/api/challenges/{session_id}")
async def get_challenge(session_id: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    session = await challenge_center.get_session(session_id, user_id=user.id)
    if not session:
        raise HTTPException(status_code=404, detail="challenge session not found")
    return {"success": True, "session": session}


@app.post("/api/challenges/{session_id}/submit")
async def submit_challenge(session_id: str, req: ChallengeSubmitRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    session = await challenge_center.submit_code(session_id, user_id=user.id, code=req.code)
    if not session:
        raise HTTPException(status_code=404, detail="challenge session not found")
    return {"success": True, "session": session}


@app.post("/api/challenges/{session_id}/click")
async def click_challenge(session_id: str, req: ChallengeClickRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    session = await challenge_center.click(
        session_id,
        user_id=user.id,
        x=req.x,
        y=req.y,
        image_width=req.image_width,
        image_height=req.image_height,
    )
    if not session:
        raise HTTPException(status_code=404, detail="challenge session not found")
    return {"success": True, "session": session}


@app.post("/api/challenges/{session_id}/drag")
async def drag_challenge(session_id: str, req: ChallengeDragRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    session = await challenge_center.drag(
        session_id,
        user_id=user.id,
        from_x=req.from_x,
        from_y=req.from_y,
        to_x=req.to_x,
        to_y=req.to_y,
        image_width=req.image_width,
        image_height=req.image_height,
        steps=req.steps,
    )
    if not session:
        raise HTTPException(status_code=404, detail="challenge session not found")
    return {"success": True, "session": session}


@app.post("/api/challenges/{session_id}/refresh")
async def refresh_challenge(session_id: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    session = await challenge_center.refresh(session_id, user_id=user.id)
    if not session:
        raise HTTPException(status_code=404, detail="challenge session not found")
    return {"success": True, "session": session}


@app.post("/api/challenges/{session_id}/close")
async def close_challenge(session_id: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    session = await challenge_center.close(session_id, user_id=user.id)
    if not session:
        raise HTTPException(status_code=404, detail="challenge session not found")
    return {"success": True, "session": session}


@app.get("/api/challenges/{session_id}/screenshot")
async def get_challenge_screenshot(session_id: str, user: User = Depends(get_current_user)):
    session = await challenge_center.get_session(session_id, user_id=user.id)
    if not session:
        raise HTTPException(status_code=404, detail="challenge session not found")
    screenshot_path = Path(str(session.get("screenshot_path") or ""))
    if not screenshot_path.exists():
        raise HTTPException(status_code=404, detail="challenge screenshot not found")
    return FileResponse(screenshot_path)


@app.get("/api/challenges/{session_id}/form-fields")
async def get_challenge_form_fields(session_id: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    payload = await challenge_center.inspect_form(
        session_id,
        user_id=user.id,
        profile=_build_autofill_profile(user),
    )
    if not payload:
        raise HTTPException(status_code=404, detail="challenge session not found")
    return {"success": True, **payload}


@app.post("/api/challenges/{session_id}/autofill")
async def autofill_challenge_form(
    session_id: str,
    req: ChallengeAutofillRequest,
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    payload = await challenge_center.autofill_form(
        session_id,
        user_id=user.id,
        profile=_build_autofill_profile(user, req.overrides),
        overrides=req.overrides,
    )
    if not payload:
        raise HTTPException(status_code=404, detail="challenge session not found")
    return {"success": True, **payload}


@app.post("/api/boss/challenge/start")
async def start_boss_challenge(
    keyword: str = Query(..., min_length=1),
    city: str = Query("全国"),
    max_count: int = Query(10, ge=1, le=50),
    greeting_template: str = "",
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    session = await challenge_center.start_session(
        user_id=user.id,
        url="https://www.zhipin.com/",
        title="Boss Challenge Session",
        provider="boss_playwright",
        cookie_file=str(BOSS_COOKIES_FILE),
        metadata={
            "task_type": "boss_apply",
            "keyword": keyword,
            "city": city,
            "max_count": max_count,
            "greeting_template": greeting_template,
        },
    )
    _save_pending_task(
        session["id"],
        {
            "type": "boss_apply",
            "user_id": user.id,
            "keyword": keyword,
            "city": city,
            "max_count": max_count,
            "greeting_template": greeting_template,
            "created_at": _utc_now().isoformat(),
        },
    )
    return {"success": True, "session": session}


@app.post("/api/boss/challenge/{session_id}/resume")
async def resume_boss_challenge(session_id: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    session = await challenge_center.refresh(session_id, user_id=user.id)
    if not session:
        raise HTTPException(status_code=404, detail="challenge session not found")
    if session.get("state") not in {"ready", "resumed"}:
        raise HTTPException(status_code=409, detail="challenge session is not ready to resume")

    task = _get_pending_task(session_id)
    if not task or str(task.get("user_id") or "") != user.id:
        raise HTTPException(status_code=404, detail="pending boss task not found")

    runtime = challenge_center.get_runtime(session_id, user_id=user.id)
    if runtime is None:
        raise HTTPException(status_code=409, detail="challenge browser runtime is not available")

    result = await boss_bridge.batch_apply_async(
        str(task.get("keyword") or ""),
        str(task.get("city") or "??"),
        int(task.get("max_count") or 10),
        str(task.get("greeting_template") or ""),
        runtime=runtime,
        runtime_session_id=session_id,
    )
    result_state = str(result.get("state") or "")
    if result_state in {"challenge_required", "waiting_human"} or result.get("busy"):
        latest_session = await challenge_center.refresh(session_id, user_id=user.id)
        return {
            "success": False,
            "requires_human": True,
            "result": result,
            "message": "Boss apply hit another human checkpoint. Pending task is still open.",
            "session": latest_session,
        }

    _delete_pending_task(session_id)
    await challenge_center.close(session_id, user_id=user.id)
    return {"success": True, "result": result}

@app.post("/api/analysis/resume")
async def analyze_resume(req: ResumeAnalysisRequest) -> Dict[str, Any]:
    text = str(req.resume_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="resume_text is required")
    results = await _build_resume_analysis_results(text, req.analysis_type)
    return {"success": True, "results": results, "message": "analysis completed"}


@app.get("/api/auth/providers")
async def auth_providers() -> Dict[str, Any]:
    auth_meta = _auth_mode_info()
    return {
        "success": True,
        "auth_mode": auth_meta["mode"],
        "auth_env": auth_meta["env"],
        "debug_code_exposed": auth_meta["debug_code_exposed"],
        "bypass_code_configured": auth_meta["bypass_code_configured"],
        "production_mode": auth_meta["production_mode"],
        "primary_provider": _primary_auth_provider(),
        "providers": {
            "local_account": {
                "enabled": LOCAL_ACCOUNT_AUTH_ENABLED,
                "mode": "password",
                "requires_password": True,
                "environment": APP_ENV,
                "help_text": "Local email and password registration/login backed by the persisted auth store.",
            },
            "email_direct": {
                "enabled": EMAIL_DIRECT_AUTH_ENABLED,
                "mode": "direct_login",
                "requires_code": False,
                "environment": APP_ENV,
                "limits": {
                    "ip_window_seconds": EMAIL_DIRECT_IP_WINDOW_SECONDS,
                    "ip_max_attempts": EMAIL_DIRECT_IP_MAX_ATTEMPTS,
                    "email_window_seconds": EMAIL_DIRECT_EMAIL_WINDOW_SECONDS,
                    "email_max_attempts": EMAIL_DIRECT_EMAIL_MAX_ATTEMPTS,
                    "signup_window_seconds": EMAIL_DIRECT_SIGNUP_WINDOW_SECONDS,
                    "ip_max_new_users": EMAIL_DIRECT_IP_MAX_NEW_USERS,
                },
                "help_text": "Direct email login is enabled for low-friction onboarding. Add email verification or magic links later if abuse becomes a problem.",
            },
            "sms_code": {
                "provider": {
                    "key": sms_provider.key,
                    "name": sms_provider.name,
                    "configured": sms_provider.configured,
                    "help_text": sms_provider.help_text,
                },
                "mode": _sms_auth_mode(),
                "debug_code_exposed": EXPOSE_DEBUG_CODE,
                "debug_only_bypass": EXPOSE_DEBUG_CODE and bool(AUTH_BYPASS_CODE),
                "environment": APP_ENV,
            }
        },
    }


@app.post("/api/auth/send-code")
async def send_verification_code(phone: str = Query(..., min_length=11, max_length=20)) -> Dict[str, Any]:
    normalized_phone = str(phone or "").strip()
    code = _generate_verification_code()
    _store_verification_code(normalized_phone, code)
    delivered = sms_provider.send_code(normalized_phone, code)
    sms_delivery = {
        "provider_key": sms_provider.key,
        "provider_name": sms_provider.name,
        "configured": sms_provider.configured,
        "status": "sent" if delivered else "pending",
        "help_text": sms_provider.help_text,
    }

    auth_meta = _auth_mode_info()
    send_message = "Verification code issued."
    if sms_provider.configured and delivered:
        send_message = "Verification code sent over SMS."
    elif sms_provider.configured and not delivered:
        send_message = "Verification code issued, but SMS delivery failed. Check provider credentials and logs."
    elif EXPOSE_DEBUG_CODE:
        send_message = "Verification code issued in debug mode."
    else:
        send_message = "Verification code issued. SMS gateway is not configured yet."
    payload: Dict[str, Any] = {
        "success": True,
        "message": send_message,
        "expires_in": CODE_TTL_SECONDS,
        "auth_mode": _sms_auth_mode(),
        "auth_env": auth_meta["env"],
        "debug_code_exposed": auth_meta["debug_code_exposed"],
        "bypass_code_configured": auth_meta["bypass_code_configured"],
        "production_mode": auth_meta["production_mode"],
        "sms_delivery": sms_delivery,
    }
    if EXPOSE_DEBUG_CODE:
        payload["debug_code"] = code
    return payload


@app.post("/api/auth/register")
async def register(req: RegisterRequest) -> Dict[str, Any]:
    if not _validate_verification_code(req.phone, req.code):
        raise HTTPException(status_code=400, detail="invalid verification code")
    if _get_user_by_phone(req.phone):
        raise HTTPException(status_code=400, detail="phone already registered")

    user = User(
        id=str(uuid.uuid4()),
        phone=req.phone.strip(),
        nickname=(req.nickname or req.phone).strip(),
        plan="free",
        remaining_quota=5,
        created_at=_utc_now(),
    )
    users_db[user.id] = user
    _consume_verification_code(req.phone)
    _persist_all()
    token = _create_token(user.id)
    auth_meta = _auth_mode_info()
    return {
        "success": True,
        "token": token,
        "user": _serialize_user(user),
        "auth_mode": _sms_auth_mode(),
        "auth_env": auth_meta["env"],
        "production_mode": auth_meta["production_mode"],
    }


@app.post("/api/auth/login")
async def login(req: LoginRequest) -> Dict[str, Any]:
    if not _validate_verification_code(req.phone, req.code):
        raise HTTPException(status_code=400, detail="invalid verification code")
    user = _get_user_by_phone(req.phone)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    _consume_verification_code(req.phone)
    token = _create_token(user.id)
    auth_meta = _auth_mode_info()
    return {
        "success": True,
        "token": token,
        "user": _serialize_user(user),
        "auth_mode": _sms_auth_mode(),
        "auth_env": auth_meta["env"],
        "production_mode": auth_meta["production_mode"],
    }


@app.post("/api/auth/email-login")
async def email_login(req: EmailLoginRequest, request: Request) -> Dict[str, Any]:
    if not EMAIL_DIRECT_AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="email direct auth is disabled")
    email = _normalize_email(req.email)
    if not _validate_email_address(email):
        raise HTTPException(status_code=400, detail="invalid email")

    user = _get_user_by_email(email)
    _enforce_email_direct_limits(request, email, is_new_user=user is None)
    if not user:
        nickname_seed = (req.nickname or email.split("@", 1)[0] or "user").strip()
        user = User(
            id=str(uuid.uuid4()),
            phone="",
            email=email,
            nickname=nickname_seed,
            plan="free",
            remaining_quota=max(0, EMAIL_DIRECT_NEW_USER_QUOTA),
            created_at=_utc_now(),
        )
        users_db[user.id] = user
        _persist_all()

    token = _create_token(user.id)
    auth_meta = _auth_mode_info()
    return {
        "success": True,
        "token": token,
        "user": _serialize_user(user),
        "auth_mode": "email_direct",
        "auth_env": auth_meta["env"],
        "production_mode": auth_meta["production_mode"],
    }


@app.post("/api/auth/local-register")
async def local_register(req: LocalRegisterRequest) -> Dict[str, Any]:
    if not LOCAL_ACCOUNT_AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="local account auth is disabled")
    email = _normalize_email(req.email)
    if not _validate_email_address(email):
        raise HTTPException(status_code=400, detail="invalid email")
    if not _validate_password_strength(req.password):
        raise HTTPException(status_code=400, detail="password must be at least 8 characters")
    existing_user = _get_user_by_email(email)
    if existing_user:
        existing_credentials = _get_credentials_by_user_id(existing_user.id)
        if existing_credentials:
            raise HTTPException(status_code=400, detail="email already registered")
        credentials_db[existing_user.id] = _hash_password(req.password)
        if req.nickname:
            existing_user.nickname = req.nickname.strip() or existing_user.nickname
            users_db[existing_user.id] = existing_user
        _persist_all()
        token = _create_token(existing_user.id)
        auth_meta = _auth_mode_info()
        return {
            "success": True,
            "token": token,
            "user": _serialize_user(existing_user),
            "auth_mode": "local_account",
            "auth_env": auth_meta["env"],
            "production_mode": auth_meta["production_mode"],
        }

    nickname_seed = (req.nickname or email.split("@", 1)[0] or "user").strip()
    user = User(
        id=str(uuid.uuid4()),
        phone="",
        email=email,
        nickname=nickname_seed,
        plan="free",
        remaining_quota=max(0, EMAIL_DIRECT_NEW_USER_QUOTA),
        created_at=_utc_now(),
    )
    users_db[user.id] = user
    credentials_db[user.id] = _hash_password(req.password)
    _persist_all()

    token = _create_token(user.id)
    auth_meta = _auth_mode_info()
    return {
        "success": True,
        "token": token,
        "user": _serialize_user(user),
        "auth_mode": "local_account",
        "auth_env": auth_meta["env"],
        "production_mode": auth_meta["production_mode"],
    }


@app.post("/api/auth/local-login")
async def local_login(req: LocalLoginRequest) -> Dict[str, Any]:
    if not LOCAL_ACCOUNT_AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="local account auth is disabled")
    email = _normalize_email(req.email)
    if not _validate_email_address(email):
        raise HTTPException(status_code=400, detail="invalid email")

    user = _get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    credentials = _get_credentials_by_user_id(user.id)
    if not _verify_password(credentials, req.password):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = _create_token(user.id)
    auth_meta = _auth_mode_info()
    return {
        "success": True,
        "token": token,
        "user": _serialize_user(user),
        "auth_mode": "local_account",
        "auth_env": auth_meta["env"],
        "production_mode": auth_meta["production_mode"],
    }


@app.get("/api/user/info")
async def get_user_info(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {"success": True, "user": _serialize_user(user)}


@app.post("/api/auth/change-password")
async def change_password(req: ChangePasswordRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    if not LOCAL_ACCOUNT_AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="local account auth is disabled")
    if not user.email:
        raise HTTPException(status_code=400, detail="current account has no email")
    if not _validate_password_strength(req.new_password):
        raise HTTPException(status_code=400, detail="new password must be at least 8 characters")

    existing_credentials = _get_credentials_by_user_id(user.id)
    if existing_credentials:
        if not req.current_password:
            raise HTTPException(status_code=400, detail="current password is required")
        if not _verify_password(existing_credentials, req.current_password):
            raise HTTPException(status_code=401, detail="current password is incorrect")

    credentials_db[user.id] = _hash_password(req.new_password)
    _persist_all()
    return {"success": True, "message": "password updated"}


@app.post("/api/user/upgrade")
async def upgrade_plan(req: UpgradeRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    if not ALLOW_SELF_SERVE_UPGRADE:
        raise HTTPException(status_code=403, detail="self-serve upgrade is disabled")
    plans = {
        "basic": {"quota": 30, "days": 30},
        "pro": {"quota": 100, "days": 30},
        "yearly": {"quota": 999999, "days": 365},
    }
    if req.plan not in plans:
        raise HTTPException(status_code=400, detail="unknown plan")
    plan_info = plans[req.plan]
    user.plan = req.plan
    user.remaining_quota = plan_info["quota"]
    user.expired_at = _utc_now() + timedelta(days=plan_info["days"])
    users_db[user.id] = user
    _persist_all()
    return {
        "success": True,
        "message": f"plan upgraded to {req.plan}",
        "user": _serialize_user(user),
    }


@app.post("/api/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    original_name = _sanitize_filename(file.filename or "resume")
    file_path = UPLOAD_DIR / f"{user.id}__{original_name}"
    content = await file.read()
    file_path.write_bytes(content)

    try:
        text = extract_text_from_file(file_path)
    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"failed to parse resume: {exc}") from exc

    if not str(text or "").strip():
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="resume text is empty after parsing")

    hr_store.upsert_candidate(_candidate_payload_from_resume(user, text, original_name))
    return {"success": True, "filename": original_name, "text": text}


@app.get("/api/resume/list")
async def list_resumes(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    rows = []
    prefix = f"{user.id}__"
    for file_path in sorted(UPLOAD_DIR.glob(f"{prefix}*")):
        rows.append(
            {
                "filename": file_path.name[len(prefix):],
                "size": file_path.stat().st_size,
                "path": str(file_path),
            }
        )
    return {"success": True, "resumes": rows}


@app.get("/api/resume/text/{filename}")
async def get_resume_text(filename: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    safe_name = _sanitize_filename(filename)
    file_path = UPLOAD_DIR / f"{user.id}__{safe_name}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="resume not found")
    text = extract_text_from_file(file_path)
    return {"success": True, "filename": safe_name, "text": text}


@app.delete("/api/resume/{filename}")
async def delete_resume(filename: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    safe_name = _sanitize_filename(filename)
    file_path = UPLOAD_DIR / f"{user.id}__{safe_name}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="resume not found")
    file_path.unlink()
    return {"success": True, "filename": safe_name}


@app.get("/api/jobs/search")
async def jobs_search(
    keyword: str = Query(..., min_length=1),
    city: str = Query("全国"),
    max_count: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: jobs_bridge.search_jobs(keyword=keyword, city=city, limit=max_count))
    normalized_jobs = [_to_legacy_openclaw_job(job, city, index) for index, job in enumerate(result.jobs, 1)]
    normalized_jobs = [{**job, "apply_target": _is_direct_apply_target(job)} for job in normalized_jobs]
    _cache_jobs(normalized_jobs)
    assisted_status = "challenge_required" if result.provider == "openclaw_challenge" else "standby"
    return {
        "success": True,
        "jobs": normalized_jobs,
        "total": len(normalized_jobs),
        "apply_ready_count": sum(1 for job in normalized_jobs if job.get("apply_target")),
        "provider": result.provider,
        "warning": result.warning,
        "assisted_status": assisted_status,
    }


@app.get("/api/boss/status")
async def boss_status() -> Dict[str, Any]:
    return {"success": True, **boss_bridge.status()}


@app.post("/api/boss/login")
async def boss_login() -> Dict[str, Any]:
    result = await asyncio.to_thread(boss_bridge.login)
    return {"success": bool(result.get("success")), **result}


@app.get("/api/boss/search")
async def boss_search(
    keyword: str = Query(..., min_length=1),
    city: str = Query("全国"),
    max_count: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    result = await asyncio.to_thread(boss_bridge.search_jobs, keyword, city, max_count)
    return result


@app.post("/api/boss/apply")
async def boss_apply(
    keyword: str = Query(..., min_length=1),
    city: str = Query("全国"),
    max_count: int = Query(10, ge=1, le=50),
    greeting_template: str = "",
) -> Dict[str, Any]:
    result = await asyncio.to_thread(boss_bridge.batch_apply, keyword, city, max_count, greeting_template)
    return result


@app.get("/api/hr/overview")
async def hr_overview(hr_id: str = "") -> Dict[str, Any]:
    return {"success": True, **hr_store.overview(hr_id=hr_id)}


@app.post("/api/hr/jobs")
async def create_hr_job(req: HRJobRequest) -> Dict[str, Any]:
    job = hr_store.create_job(req.model_dump() if hasattr(req, "model_dump") else req.dict())
    return {"success": True, "job": job}


@app.get("/api/hr/jobs")
async def list_hr_jobs(hr_id: str = "", limit: int = 50) -> Dict[str, Any]:
    jobs = hr_store.list_jobs(hr_id=hr_id, limit=limit)
    return {"success": True, "jobs": jobs}


@app.get("/api/hr/candidates/match")
async def hr_candidates_match(job_id: str, hr_id: str = "", limit: int = 50) -> Dict[str, Any]:
    try:
        matches = hr_store.match_candidates(job_id=job_id, hr_id=hr_id, limit=limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True, "candidates": matches}


@app.post("/api/hr/actions")
async def hr_actions(req: HRActionRequest) -> Dict[str, Any]:
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    action = hr_store.record_action("hr", payload)
    return {"success": True, "action": action}


@app.post("/api/candidate/actions")
async def candidate_actions(req: HRActionRequest) -> Dict[str, Any]:
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    action = hr_store.record_action("candidate", payload)
    return {"success": True, "action": action}


@app.get("/api/hr/mutual-matches")
async def hr_mutual_matches(hr_id: str = "", job_id: str = "", limit: int = 100) -> Dict[str, Any]:
    matches = hr_store.list_mutual_matches(hr_id=hr_id, job_id=job_id, limit=limit)
    return {"success": True, "matches": matches}


@app.websocket("/api/apply/ws")
async def websocket_apply(websocket: WebSocket) -> None:
    await websocket.accept()
    connection_id = uuid.uuid4().hex
    active_connections[connection_id].append(websocket)
    slot_user_id = ""
    slot_client_ip = ""

    try:
        data = await websocket.receive_json()
        token = str(data.get("token") or "").strip()
        user_id = _verify_token(token)
        user = users_db.get(user_id or "")
        if not user:
            await websocket.send_json({"error": True, "message": "not logged in"})
            return
        slot_user_id = user.id
        slot_client_ip = _extract_websocket_ip(websocket)
        _acquire_apply_slot(slot_user_id, slot_client_ip)

        keyword = str(data.get("keyword") or "").strip()
        city = str(data.get("city") or "全国").strip()
        resume_text = str(data.get("resume_text") or "").strip()
        max_count = min(int(data.get("max_count") or 10), user.remaining_quota)
        apply_mode = str(data.get("apply_mode") or "").strip().lower()

        if not keyword:
            await websocket.send_json({"error": True, "message": "keyword is required"})
            return
        if not resume_text:
            await websocket.send_json({"error": True, "message": "resume_text is required"})
            return
        if max_count <= 0:
            await websocket.send_json({"error": True, "message": "quota exhausted"})
            return

        await websocket.send_json(
            {
                "stage": "searching",
                "message": f"searching jobs for {keyword}",
                "progress": 0.1,
            }
        )
        jobs_result = await asyncio.to_thread(jobs_bridge.search_jobs, keyword, city, max_count)
        jobs = [job for job in jobs_result.jobs if _is_direct_apply_target(job)]
        _cache_jobs([_to_legacy_openclaw_job(job, city, index) for index, job in enumerate(jobs, 1)])
        await websocket.send_json(
            {
                "stage": "found",
                "message": f"found {len(jobs)} jobs",
                "progress": 0.3,
                "job_count": len(jobs),
                "provider": jobs_result.provider,
                "warning": jobs_result.warning,
                "assisted_status": "challenge_required" if jobs_result.provider == "openclaw_challenge" else "standby",
            }
        )

        if apply_mode == "boss_assisted":
            assisted = await asyncio.to_thread(boss_bridge.batch_apply, keyword, city, max_count, "")
            attempted = min(
                user.remaining_quota,
                int(assisted.get("success", 0) or 0) + int(assisted.get("failed", 0) or 0),
            )
            if attempted > 0:
                user.remaining_quota = max(0, user.remaining_quota - attempted)
                users_db[user.id] = user
                _persist_all()
            details = assisted.get("details", []) or []
            for item in details:
                _record_application(
                    user.id,
                    job_title=str(item.get("job") or keyword),
                    company=str(item.get("company") or "Boss"),
                    status="success" if item.get("success") else "failed",
                    source="boss_assisted",
                    detail=str(item.get("message") or assisted.get("message") or ""),
                    job_id=str(item.get("job_id") or item.get("id") or ""),
                    mode="boss_assisted",
                )
            if not details:
                for index in range(max(0, int(assisted.get("success", 0) or 0))):
                    _record_application(
                        user.id,
                        job_title=keyword,
                        company="Boss",
                        status="success",
                        source="boss_assisted",
                        detail=str(assisted.get("message") or ""),
                        job_id=f"boss_success_{index + 1}",
                        mode="boss_assisted",
                    )
                for index in range(max(0, int(assisted.get("failed", 0) or 0))):
                    _record_application(
                        user.id,
                        job_title=keyword,
                        company="Boss",
                        status="failed",
                        source="boss_assisted",
                        detail=str(assisted.get("message") or ""),
                        job_id=f"boss_failed_{index + 1}",
                        mode="boss_assisted",
                    )
            await websocket.send_json(
                {
                    "stage": "completed",
                    "message": assisted.get("message", "boss assisted apply finished"),
                    "progress": 1.0,
                    "success_count": assisted.get("success", 0),
                    "failed_count": assisted.get("failed", 0),
                    "remaining_quota": user.remaining_quota,
                    "mode": "boss_assisted",
                    "details": assisted.get("details", []),
                    "assisted_status": assisted.get("state", "waiting_human"),
                }
            )
            return

        success_count = 0
        failed_count = 0
        await websocket.send_json(
            {
                "stage": "applying",
                "message": "starting apply flow",
                "progress": 0.4,
                "mode": "simulation" if ALLOW_SIMULATED_APPLY else "strict",
            }
        )

        for index, job in enumerate(jobs, 1):
            if user.remaining_quota <= 0:
                break
            user.remaining_quota = max(0, user.remaining_quota - 1)
            users_db[user.id] = user
            _persist_all()
            greeting = await generate_greeting(job, resume_text)
            success = await apply_single_job(job, greeting)
            if success:
                success_count += 1
            else:
                failed_count += 1
            _record_application(
                user.id,
                job_title=str(job.get("title") or ""),
                company=str(job.get("company") or ""),
                status="success" if success else "failed",
                source=str(job.get("source") or job.get("provider") or ""),
                url=str(job.get("url") or job.get("link") or ""),
                detail=greeting,
                job_id=str(job.get("job_id") or job.get("id") or ""),
                mode="apply_ws",
            )

            progress = 0.4 + (index / max(1, len(jobs))) * 0.6
            await websocket.send_json(
                {
                    "stage": "applying",
                    "current": index,
                    "total": len(jobs),
                    "progress": progress,
                    "job": job.get("title", ""),
                    "company": job.get("company", ""),
                    "greeting": greeting,
                    "success": success,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "remaining_quota": user.remaining_quota,
                    "url": job.get("url", ""),
                    "source": job.get("source", ""),
                }
            )

        await websocket.send_json(
            {
                "stage": "completed",
                "message": f"completed: success={success_count}, failed={failed_count}",
                "progress": 1.0,
                "success_count": success_count,
                "failed_count": failed_count,
                "remaining_quota": user.remaining_quota,
            }
        )
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"error": True, "message": str(exc)})
        except Exception:
            pass
    finally:
        active_connections.pop(connection_id, None)
        if slot_user_id:
            _release_apply_slot(slot_user_id, slot_client_ip)
        try:
            await websocket.close()
        except Exception:
            pass


@app.websocket("/api/apply/ws/apply")
async def websocket_apply_selected_jobs(websocket: WebSocket) -> None:
    await websocket.accept()
    slot_user_id = ""
    slot_client_ip = ""
    user: Optional[User] = None
    try:
        data = await websocket.receive_json()
        user = _extract_optional_user_from_websocket(websocket, data)
        if user is not None:
            slot_user_id = user.id
            slot_client_ip = _extract_websocket_ip(websocket)
            _acquire_apply_slot(slot_user_id, slot_client_ip)

        resume_text = str(data.get("resume_text") or "").strip()
        if not resume_text:
            await websocket.send_json({"error": True, "message": "resume_text is required"})
            return

        selected_jobs = data.get("selected_jobs") or data.get("jobs") or []
        job_ids = data.get("job_ids") or []
        jobs: List[Dict[str, Any]] = []
        if isinstance(selected_jobs, list):
            jobs.extend([dict(item) for item in selected_jobs if isinstance(item, dict)])
        if isinstance(job_ids, list):
            for value in job_ids:
                candidate = str(value or "").strip()
                if not candidate:
                    continue
                cached = _job_from_cache(candidate)
                if cached:
                    jobs.append(cached)
                else:
                    jobs.append(
                        {
                            "job_id": candidate,
                            "id": candidate,
                            "title": f"Job {candidate}",
                            "company": "",
                            "location": "",
                            "source": "job_id_only",
                        }
                    )
        if not jobs:
            await websocket.send_json({"error": True, "message": "job_ids or selected_jobs is required"})
            return

        unique_jobs: List[Dict[str, Any]] = []
        seen_job_ids: set[str] = set()
        for index, job in enumerate(jobs, 1):
            normalized = _to_legacy_openclaw_job(job, str(job.get("location") or ""), index)
            candidate_id = str(normalized.get("job_id") or normalized.get("id") or "")
            if not candidate_id or candidate_id in seen_job_ids:
                continue
            seen_job_ids.add(candidate_id)
            unique_jobs.append(normalized)

        if not unique_jobs:
            await websocket.send_json({"error": True, "message": "no valid jobs to apply"})
            return

        unique_jobs = [job for job in unique_jobs if _is_direct_apply_target(job)]
        if not unique_jobs:
            await websocket.send_json({"error": True, "message": "no direct-apply job detail targets available"})
            return

        max_quota = user.remaining_quota if user is not None else len(unique_jobs)
        total = min(len(unique_jobs), max_quota)
        if total <= 0:
            await websocket.send_json({"error": True, "message": "quota exhausted"})
            return

        use_ai = bool(data.get("use_ai_cover_letter", True))
        success_count = 0
        failed_count = 0
        for index, job in enumerate(unique_jobs[:total], 1):
            if user is not None:
                user.remaining_quota = max(0, user.remaining_quota - 1)
                users_db[user.id] = user
                _persist_all()

            if use_ai:
                greeting = await generate_greeting(job, resume_text)
            else:
                title = str(job.get("title") or "this role")
                company = str(job.get("company") or "your company")
                greeting = f"Hello, I am interested in {title} at {company}."
            success = await apply_single_job(job, greeting)
            if success:
                success_count += 1
            else:
                failed_count += 1

            _record_application(
                user.id if user is not None else "",
                job_title=str(job.get("title") or ""),
                company=str(job.get("company") or ""),
                status="success" if success else "failed",
                source=str(job.get("source") or job.get("provider") or "selected_jobs"),
                detail=greeting,
                job_id=str(job.get("job_id") or job.get("id") or ""),
                mode="apply_ws_selected",
            )

            progress_payload: Dict[str, Any] = {
                "current": index,
                "total": total,
                "progress": index / max(total, 1),
                "job": str(job.get("title") or ""),
                "company": str(job.get("company") or ""),
                "success": success,
                "success_count": success_count,
                "failed_count": failed_count,
                "assisted_status": "standby",
            }
            if user is not None:
                progress_payload["remaining_quota"] = user.remaining_quota
            await websocket.send_json(progress_payload)

        completion_message = f"completed: success={success_count}, failed={failed_count}"
        if len(unique_jobs) > total:
            completion_message += f", skipped={len(unique_jobs) - total} (quota)"

        completion_payload: Dict[str, Any] = {
            "completed": True,
            "message": completion_message,
            "success": success_count,
            "failed": failed_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "assisted_status": "resumed" if success_count else "standby",
        }
        if user is not None:
            completion_payload["remaining_quota"] = user.remaining_quota
        await websocket.send_json(completion_payload)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"error": True, "message": str(exc)})
        except Exception:
            pass
    finally:
        if slot_user_id:
            _release_apply_slot(slot_user_id, slot_client_ip)
        try:
            await websocket.close()
        except Exception:
            pass


@app.get("/app", include_in_schema=False)
async def frontend_workspace():
    if _frontend_available():
        return FileResponse(FRONTEND_INDEX_FILE)
    raise HTTPException(status_code=404, detail="frontend build missing")


@app.get("/{full_path:path}", include_in_schema=False)
async def frontend_catch_all(full_path: str):
    if not _frontend_available():
        raise HTTPException(status_code=404, detail="frontend build missing")

    candidate = FRONTEND_DIST_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)

    return FileResponse(FRONTEND_INDEX_FILE)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8765)
