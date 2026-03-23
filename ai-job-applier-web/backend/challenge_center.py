from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright


ACTIVE_STATES = {"checking", "challenge_required", "ready", "resumed"}
FINAL_STATES = {"closed", "expired", "failed"}
SESSION_TTL = timedelta(minutes=20)
CLOSED_RETENTION = timedelta(hours=12)
MAX_ACTIVE_SESSIONS_PER_USER = 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(value: Any) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


class ChallengeCenter:
    def __init__(self, store_file: Path, snapshot_dir: Path) -> None:
        self.store_file = Path(store_file)
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._sessions: Dict[str, Dict[str, Any]] = self._load_store()
        self._runtime: Dict[str, Dict[str, Any]] = {}
        self._playwright = None

    def _load_store(self) -> Dict[str, Dict[str, Any]]:
        if not self.store_file.exists():
            return {}
        try:
            raw = json.loads(self.store_file.read_text(encoding="utf-8") or "{}")
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        return {str(key): dict(value) for key, value in raw.items() if isinstance(value, dict)}

    def _save_store(self) -> None:
        self.store_file.parent.mkdir(parents=True, exist_ok=True)
        self.store_file.write_text(
            json.dumps(self._sessions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def _ensure_playwright(self):
        if self._playwright is not None:
            return self._playwright
        self._playwright = await async_playwright().start()
        return self._playwright

    def _runtime_alive(self, session_id: str) -> bool:
        runtime = self._runtime.get(session_id)
        if not runtime:
            return False
        page = runtime.get("page")
        browser = runtime.get("browser")
        if page is None or browser is None:
            return False
        try:
            if page.is_closed():
                return False
        except Exception:
            return False
        try:
            if not browser.is_connected():
                return False
        except Exception:
            return False
        return True

    async def _close_runtime(self, session_id: str) -> None:
        runtime = self._runtime.pop(session_id, None)
        if not runtime:
            return
        try:
            await runtime["context"].close()
        except Exception:
            pass
        try:
            await runtime["browser"].close()
        except Exception:
            pass

    async def _load_cookies(self, context, cookie_file: str) -> None:
        raw_path = str(cookie_file or "").strip()
        if not raw_path:
            return
        target = Path(raw_path)
        if not target.exists():
            return
        try:
            cookies = json.loads(target.read_text(encoding="utf-8") or "[]")
        except Exception:
            return
        if not isinstance(cookies, list) or not cookies:
            return
        try:
            await context.add_cookies(cookies)
        except Exception:
            return

    async def _persist_cookies(self, session_id: str) -> None:
        session = self._sessions.get(session_id, {})
        cookie_file = str(session.get("cookie_file") or "").strip()
        runtime = self._runtime.get(session_id)
        if not cookie_file or not runtime:
            return
        try:
            cookies = await runtime["context"].cookies()
        except Exception:
            return
        try:
            target = Path(cookie_file)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            return

    async def _safe_navigate(self, page, url: str) -> None:
        attempts = (
            ("domcontentloaded", 45000, 2500),
            ("commit", 15000, 3000),
        )
        for wait_until, timeout_ms, settle_ms in attempts:
            try:
                await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                await page.wait_for_timeout(settle_ms)
                return
            except Exception:
                continue
        await page.wait_for_timeout(5000)

    async def _relaunch_runtime(self, session_id: str) -> bool:
        session = self._sessions.get(session_id, {})
        target_url = str(session.get("target_url") or "").strip()
        if not target_url:
            return False

        await self._close_runtime(session_id)
        playwright = await self._ensure_playwright()
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        await self._load_cookies(context, str(session.get("cookie_file") or ""))
        page = await context.new_page()
        await self._safe_navigate(page, target_url)
        self._runtime[session_id] = {
            "browser": browser,
            "context": context,
            "page": page,
        }
        return True

    async def _stabilize_session_start(self, session_id: str) -> Dict[str, Any]:
        session = self._sessions.get(session_id, {})
        target_url = str(session.get("target_url") or "").strip()
        runtime = self._runtime.get(session_id)
        if not runtime:
            return dict(session)

        page = runtime["page"]
        last_state: Dict[str, Any] = {}
        for _ in range(4):
            last_state = await self._refresh_session(session_id)
            current_url = str(last_state.get("current_url") or "").strip().lower()
            state = str(last_state.get("state") or "")
            if state != "checking" and current_url not in {"", "about:blank"}:
                return last_state
            if target_url:
                try:
                    await self._safe_navigate(page, target_url)
                except Exception:
                    pass

        last_state = await self._refresh_session(session_id)
        current_url = str(last_state.get("current_url") or "").strip().lower()
        if current_url in {"", "about:blank"}:
            relaunched = await self._relaunch_runtime(session_id)
            if relaunched:
                last_state = await self._refresh_session(session_id)
                current_url = str(last_state.get("current_url") or "").strip().lower()
        if current_url in {"", "about:blank"}:
            last_state["state"] = "failed"
            last_state["message"] = "Failed to reach the target page."
            last_state["updated_at"] = _utc_now()
            self._sessions[session_id] = last_state
            self._save_store()
        return last_state

    async def _detect_challenge(self, page) -> tuple[str, str]:
        url = str(page.url or "").strip().lower()
        if not url or url == "about:blank":
            return "checking", "Page navigation is still in progress."

        try:
            title = (await page.title()).lower()
        except Exception:
            title = ""
        try:
            content = (await page.content()).lower()
        except Exception:
            content = ""

        markers = (
            "captcha",
            "verify",
            "challenge",
            "verify-slider",
            "human verification",
            "security",
            "safe/verify",
            "passport/zp/verify",
            "滑块",
            "验证码",
            "安全验证",
        )
        haystack = " ".join((url, title, content))
        if any(marker in haystack for marker in markers):
            return "challenge_required", "Challenge detected. Human confirmation is required."
        return "ready", "Page is ready to continue."

    async def _snapshot(self, session_id: str) -> str:
        runtime = self._runtime.get(session_id)
        if not runtime:
            return ""
        snapshot_path = self.snapshot_dir / f"{session_id}.png"
        await runtime["page"].screenshot(path=str(snapshot_path), full_page=False)
        return str(snapshot_path)

    async def _cleanup_sessions(self, user_id: Optional[str] = None) -> None:
        now = datetime.now(timezone.utc)
        changed = False

        rows = sorted(
            self._sessions.items(),
            key=lambda item: _parse_ts(item[1].get("updated_at") or item[1].get("created_at")),
            reverse=True,
        )
        active_per_user: Dict[str, List[str]] = {}

        for session_id, session in rows:
            owner = str(session.get("user_id") or "")
            if user_id is not None and owner != str(user_id or ""):
                continue

            updated_at = _parse_ts(session.get("updated_at") or session.get("created_at"))
            age = now - updated_at
            state = str(session.get("state") or "")
            runtime_alive = self._runtime_alive(session_id)

            if state in FINAL_STATES and age > CLOSED_RETENTION:
                await self._close_runtime(session_id)
                self._sessions.pop(session_id, None)
                snapshot_path = Path(str(session.get("screenshot_path") or "").strip())
                if snapshot_path.exists():
                    try:
                        snapshot_path.unlink()
                    except Exception:
                        pass
                changed = True
                continue

            if runtime_alive and state in ACTIVE_STATES:
                active_per_user.setdefault(owner, []).append(session_id)

            if age > SESSION_TTL and state in ACTIVE_STATES:
                await self._close_runtime(session_id)
                session["state"] = "expired"
                session["message"] = "Challenge session expired. Start a new session."
                session["updated_at"] = _utc_now()
                self._sessions[session_id] = session
                changed = True

        for owner, active_ids in active_per_user.items():
            if len(active_ids) <= MAX_ACTIVE_SESSIONS_PER_USER:
                continue
            overflow = active_ids[MAX_ACTIVE_SESSIONS_PER_USER :]
            for session_id in overflow:
                session = self._sessions.get(session_id, {})
                await self._close_runtime(session_id)
                session["state"] = "expired"
                session["message"] = "Challenge session expired because too many active sessions were opened."
                session["updated_at"] = _utc_now()
                self._sessions[session_id] = session
                changed = True

        if changed:
            self._save_store()

    async def _refresh_session(self, session_id: str) -> Dict[str, Any]:
        session = dict(self._sessions.get(session_id, {}))
        if not session:
            return {}

        if not self._runtime_alive(session_id):
            if session.get("state") not in FINAL_STATES:
                session["state"] = "expired"
                session["message"] = "Browser runtime is no longer available."
                session["updated_at"] = _utc_now()
                self._sessions[session_id] = session
                self._save_store()
            return dict(session)

        runtime = self._runtime[session_id]
        page = runtime["page"]
        try:
            state, message = await self._detect_challenge(page)
        except Exception:
            state = str(session.get("state") or "checking")
            message = "Failed to inspect the page state."

        try:
            screenshot_path = await self._snapshot(session_id)
        except Exception:
            screenshot_path = str(session.get("screenshot_path") or "")

        session.update(
            {
                "id": session_id,
                "state": state,
                "message": message,
                "current_url": str(page.url or ""),
                "screenshot_path": screenshot_path,
                "updated_at": _utc_now(),
            }
        )
        self._sessions[session_id] = session
        self._save_store()

        if state in {"ready", "resumed"}:
            await self._persist_cookies(session_id)

        return dict(session)

    async def start_session(
        self,
        *,
        user_id: str,
        url: str,
        title: str = "",
        provider: str = "playwright",
        cookie_file: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self._cleanup_sessions(user_id=str(user_id or ""))

        for session_id, session in sorted(
            self._sessions.items(),
            key=lambda item: _parse_ts(item[1].get("updated_at") or item[1].get("created_at")),
            reverse=True,
        ):
            if str(session.get("user_id") or "") != str(user_id or ""):
                continue
            if str(session.get("provider") or "") != str(provider or ""):
                continue
            if str(session.get("target_url") or "") != str(url or ""):
                continue
            if not self._runtime_alive(session_id):
                continue
            if str(session.get("state") or "") not in ACTIVE_STATES:
                continue
            return await self._refresh_session(session_id)

        playwright = await self._ensure_playwright()
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        await self._load_cookies(context, cookie_file)
        page = await context.new_page()
        await self._safe_navigate(page, url)

        session_id = uuid.uuid4().hex
        self._runtime[session_id] = {
            "browser": browser,
            "context": context,
            "page": page,
        }
        self._sessions[session_id] = {
            "id": session_id,
            "user_id": str(user_id or ""),
            "provider": str(provider or "playwright"),
            "title": title or "Challenge Session",
            "target_url": str(url or ""),
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "state": "checking",
            "message": "Session created. Inspecting page state.",
            "current_url": str(page.url or ""),
            "screenshot_path": "",
            "cookie_file": str(cookie_file or ""),
            "metadata": dict(metadata or {}),
        }
        self._save_store()
        return await self._stabilize_session_start(session_id)

    def list_sessions(self, *, user_id: str) -> List[Dict[str, Any]]:
        rows = [
            dict(row)
            for row in self._sessions.values()
            if str(row.get("user_id") or "") == str(user_id or "")
        ]
        rows.sort(
            key=lambda row: _parse_ts(row.get("updated_at") or row.get("created_at")),
            reverse=True,
        )
        return rows

    async def get_session(self, session_id: str, *, user_id: str) -> Dict[str, Any]:
        session = dict(self._sessions.get(str(session_id or ""), {}))
        if not session or str(session.get("user_id") or "") != str(user_id or ""):
            return {}
        return await self._refresh_session(str(session_id or ""))

    def peek_session(self, session_id: str, *, user_id: str) -> Dict[str, Any]:
        session = dict(self._sessions.get(str(session_id or ""), {}))
        if not session or str(session.get("user_id") or "") != str(user_id or ""):
            return {}
        return session

    def _frame_token(self, frame) -> str:
        name = str(frame.name or "").strip()
        url = str(frame.url or "").strip()
        if name:
            return name
        if url:
            return url
        return "__main__"

    def _guess_profile_key(self, field: Dict[str, Any]) -> Optional[str]:
        tokens = " ".join(
            [
                str(field.get("label") or ""),
                str(field.get("name") or ""),
                str(field.get("id_attr") or ""),
                str(field.get("placeholder") or ""),
                str(field.get("autocomplete") or ""),
                str(field.get("type") or ""),
            ]
        ).lower()
        if not tokens:
            return None

        mapping = [
            ("email", ("email", "e-mail", "邮箱", "mail")),
            ("phone", ("phone", "mobile", "tel", "电话", "手机")),
            ("full_name", ("full name", "legal name", "name", "姓名")),
            ("location_city", ("city", "location", "address", "城市", "地点")),
            ("school", ("school", "university", "college", "学校", "学院")),
            ("degree", ("degree", "学历", "学位", "bachelor", "master", "phd")),
            ("major", ("major", "专业")),
            ("github_url", ("github",)),
            ("linkedin_url", ("linkedin",)),
            ("portfolio_url", ("portfolio", "website", "personal site", "博客", "网站")),
            ("summary", ("cover letter", "self introduction", "introduction", "summary", "about you", "why", "自我介绍", "个人介绍")),
            ("resume_text", ("resume", "cv", "履历", "简历")),
        ]

        if "company" in tokens or "employer" in tokens:
            return None

        for profile_key, keywords in mapping:
            if any(keyword in tokens for keyword in keywords):
                return profile_key
        return None

    async def _collect_form_fields(self, page) -> List[Dict[str, Any]]:
        frames = page.frames
        rows: List[Dict[str, Any]] = []
        script = """
() => {
  const cssEscape = (value) => {
    if (window.CSS && CSS.escape) return CSS.escape(String(value));
    return String(value).replace(/([ #;?%&,.+*~\\':"!^$\\[\\]()=>|\\/])/g, '\\\\$1');
  };
  const textOrEmpty = (value) => String(value || '').trim();
  const isVisible = (el) => {
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
  };
  const buildSelector = (el) => {
    if (el.id) return `#${cssEscape(el.id)}`;
    const tag = el.tagName.toLowerCase();
    const name = textOrEmpty(el.getAttribute('name'));
    const type = textOrEmpty(el.getAttribute('type')).toLowerCase();
    if (name) return `${tag}[name="${cssEscape(name)}"]${type ? `[type="${cssEscape(type)}"]` : ''}`;
    const parts = [];
    let current = el;
    while (current && current.nodeType === 1 && parts.length < 6) {
      let selector = current.tagName.toLowerCase();
      const siblings = current.parentElement ? Array.from(current.parentElement.children).filter((node) => node.tagName === current.tagName) : [];
      if (siblings.length > 1) {
        selector += `:nth-of-type(${siblings.indexOf(current) + 1})`;
      }
      parts.unshift(selector);
      current = current.parentElement;
    }
    return parts.join(' > ');
  };
  const labelText = (el) => {
    if (el.labels && el.labels.length) {
      return Array.from(el.labels).map((label) => textOrEmpty(label.innerText)).filter(Boolean).join(' ');
    }
    const forId = textOrEmpty(el.getAttribute('id'));
    if (forId) {
      const external = document.querySelector(`label[for="${cssEscape(forId)}"]`);
      if (external) return textOrEmpty(external.innerText);
    }
    const parentLabel = el.closest('label');
    if (parentLabel) return textOrEmpty(parentLabel.innerText);
    const group = el.closest('.form-item, .field, .form-group, .ant-form-item');
    if (group) {
      const label = group.querySelector('label');
      if (label) return textOrEmpty(label.innerText);
    }
    return '';
  };
  const nodes = Array.from(document.querySelectorAll('input, textarea, select'));
  return nodes.slice(0, 200).map((el, index) => {
    const tag = el.tagName.toLowerCase();
    const type = textOrEmpty(el.getAttribute('type')).toLowerCase();
    const selector = buildSelector(el);
    const required = el.required || el.getAttribute('aria-required') === 'true';
    const options = tag === 'select'
      ? Array.from(el.options || []).slice(0, 50).map((option) => ({
          label: textOrEmpty(option.textContent),
          value: textOrEmpty(option.value),
        }))
      : [];
    return {
      local_index: index,
      tag,
      type,
      selector,
      name: textOrEmpty(el.getAttribute('name')),
      id_attr: textOrEmpty(el.getAttribute('id')),
      label: labelText(el),
      placeholder: textOrEmpty(el.getAttribute('placeholder')),
      autocomplete: textOrEmpty(el.getAttribute('autocomplete')).toLowerCase(),
      required,
      visible: isVisible(el),
      enabled: !el.disabled,
      value: tag === 'select' ? textOrEmpty(el.value) : textOrEmpty(el.value),
      options,
    };
  }).filter((field) => field.visible && field.enabled && !['hidden', 'password', 'file'].includes(field.type));
}
"""
        for frame in frames:
            try:
                frame_fields = await frame.evaluate(script)
            except Exception:
                continue
            token = self._frame_token(frame)
            frame_url = str(frame.url or "")
            for field in frame_fields:
                enriched = dict(field)
                selector = str(enriched.get("selector") or "").strip()
                enriched["frame_token"] = token
                enriched["frame_url"] = frame_url
                enriched["field_id"] = f"{token}::{selector or enriched.get('local_index', 'field')}"
                rows.append(enriched)
        return rows

    def _suggest_field_value(self, field: Dict[str, Any], profile: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        profile_key = self._guess_profile_key(field)
        if not profile_key:
            return {"profile_key": None, "suggested_value": "", "confidence": 0.0, "status": "unmatched"}

        override_value = overrides.get(profile_key)
        value = override_value if override_value not in {None, ""} else profile.get(profile_key)
        if value in {None, ""}:
            return {
                "profile_key": profile_key,
                "suggested_value": "",
                "confidence": 0.0,
                "status": "review",
            }

        autocomplete = str(field.get("autocomplete") or "").strip().lower()
        confidence = 0.95 if autocomplete else 0.82
        status = "ready"
        if field.get("tag") == "select":
            options = field.get("options") or []
            if not any(str(option.get("label") or "").strip().lower() == str(value).strip().lower() or str(option.get("value") or "").strip().lower() == str(value).strip().lower() for option in options):
                status = "review"
                confidence = min(confidence, 0.6)

        return {
            "profile_key": profile_key,
            "suggested_value": str(value),
            "confidence": confidence,
            "status": status,
        }

    async def inspect_form(
        self,
        session_id: str,
        *,
        user_id: str,
        profile: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session = await self.get_session(session_id, user_id=user_id)
        if not session:
            return {}
        runtime = self._runtime.get(session_id)
        if not runtime:
            return {"session": session, "fields": [], "profile": dict(profile or {}), "summary": {"total": 0, "ready": 0, "review": 0, "unmatched": 0}}

        fields = await self._collect_form_fields(runtime["page"])
        profile_data = dict(profile or {})
        overrides_data = dict(overrides or {})
        prepared: List[Dict[str, Any]] = []
        summary = {"total": 0, "ready": 0, "review": 0, "unmatched": 0}
        for field in fields:
            suggestion = self._suggest_field_value(field, profile_data, overrides_data)
            row = {**field, **suggestion}
            prepared.append(row)
            summary["total"] += 1
            summary[str(suggestion["status"])] += 1

        session.setdefault("metadata", {})
        session["metadata"]["last_form_scan_at"] = _utc_now()
        session["metadata"]["last_form_summary"] = summary
        self._sessions[session_id] = session
        self._save_store()
        return {"session": session, "fields": prepared, "profile": profile_data, "summary": summary}

    async def autofill_form(
        self,
        session_id: str,
        *,
        user_id: str,
        profile: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session = await self.get_session(session_id, user_id=user_id)
        if not session:
            return {}
        runtime = self._runtime.get(session_id)
        if not runtime:
            return {"session": session, "filled": [], "skipped": [], "profile": dict(profile or {})}

        inspection = await self.inspect_form(
            session_id,
            user_id=user_id,
            profile=profile,
            overrides=overrides,
        )
        fields = inspection.get("fields") or []
        profile_data = dict(inspection.get("profile") or {})
        filled: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []

        page = runtime["page"]
        frames = {self._frame_token(frame): frame for frame in page.frames}

        for field in fields:
            selector = str(field.get("selector") or "").strip()
            frame = frames.get(str(field.get("frame_token") or "__main__"))
            suggested_value = str(field.get("suggested_value") or "").strip()
            profile_key = str(field.get("profile_key") or "").strip()
            status = str(field.get("status") or "")
            tag = str(field.get("tag") or "").strip().lower()
            field_type = str(field.get("type") or "").strip().lower()

            if not selector or frame is None:
                skipped.append({"field_id": field.get("field_id"), "reason": "missing_selector"})
                continue
            if not profile_key or not suggested_value:
                skipped.append({"field_id": field.get("field_id"), "reason": "no_suggestion"})
                continue
            if field_type in {"checkbox", "radio", "file"}:
                skipped.append({"field_id": field.get("field_id"), "reason": "high_risk_field"})
                continue
            if status == "review" and tag == "select":
                skipped.append({"field_id": field.get("field_id"), "reason": "select_requires_review"})
                continue

            locator = frame.locator(selector).first
            try:
                if tag == "select":
                    option_matched = False
                    for option in field.get("options") or []:
                        label = str(option.get("label") or "").strip()
                        value = str(option.get("value") or "").strip()
                        if suggested_value.lower() in {label.lower(), value.lower()}:
                            await locator.select_option(value=value or None, label=label or None)
                            option_matched = True
                            break
                    if not option_matched:
                        skipped.append({"field_id": field.get("field_id"), "reason": "select_option_not_found"})
                        continue
                else:
                    await locator.fill(suggested_value)
                    try:
                        await locator.blur()
                    except Exception:
                        pass
                filled.append(
                    {
                        "field_id": field.get("field_id"),
                        "profile_key": profile_key,
                        "value": suggested_value,
                    }
                )
            except Exception as exc:
                skipped.append({"field_id": field.get("field_id"), "reason": f"fill_failed:{exc.__class__.__name__}"})

        await page.wait_for_timeout(800)
        session = await self._refresh_session(session_id)
        session.setdefault("metadata", {})
        session["metadata"]["last_autofill_at"] = _utc_now()
        session["metadata"]["last_autofill_count"] = len(filled)
        self._sessions[session_id] = session
        self._save_store()
        return {
            "session": session,
            "fields": inspection.get("fields") or [],
            "profile": profile_data,
            "filled": filled,
            "skipped": skipped,
            "summary": {
                "filled": len(filled),
                "skipped": len(skipped),
            },
        }

    async def submit_code(self, session_id: str, *, user_id: str, code: str) -> Dict[str, Any]:
        session = await self.get_session(session_id, user_id=user_id)
        if not session:
            return {}
        runtime = self._runtime.get(session_id)
        if not runtime:
            session["state"] = "expired"
            session["message"] = "Browser runtime is no longer available."
            self._sessions[session_id] = session
            self._save_store()
            return session

        page = runtime["page"]
        input_selectors = [
            "input[type='text']",
            "input[type='tel']",
            "input[type='number']",
            "input:not([type])",
            "textarea",
        ]
        filled = False
        for selector in input_selectors:
            locator = page.locator(selector)
            count = await locator.count()
            for index in range(min(count, 5)):
                handle = locator.nth(index)
                try:
                    if await handle.is_visible() and await handle.is_enabled():
                        await handle.fill(str(code or ""))
                        filled = True
                        break
                except Exception:
                    continue
            if filled:
                break

        if not filled:
            session["state"] = "failed"
            session["message"] = "No visible text input was found on the challenge page."
            session["updated_at"] = _utc_now()
            self._sessions[session_id] = session
            self._save_store()
            return session

        clicked = False
        button_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button",
        ]
        for selector in button_selectors:
            locator = page.locator(selector)
            count = await locator.count()
            for index in range(min(count, 5)):
                handle = locator.nth(index)
                try:
                    if await handle.is_visible() and await handle.is_enabled():
                        await handle.click()
                        clicked = True
                        break
                except Exception:
                    continue
            if clicked:
                break

        if not clicked:
            try:
                await page.keyboard.press("Enter")
            except Exception:
                pass

        await page.wait_for_timeout(1200)
        session = await self._refresh_session(session_id)
        if session.get("state") == "ready":
            session["state"] = "resumed"
            session["message"] = "Challenge input submitted. Session is ready to resume."
            session["updated_at"] = _utc_now()
            self._sessions[session_id] = session
            self._save_store()
            await self._persist_cookies(session_id)
        return dict(self._sessions.get(session_id, session))

    async def click(
        self,
        session_id: str,
        *,
        user_id: str,
        x: float,
        y: float,
        image_width: float,
        image_height: float,
    ) -> Dict[str, Any]:
        session = self.peek_session(session_id, user_id=user_id)
        if not session:
            return {}
        if not self._runtime_alive(session_id):
            session["state"] = "expired"
            session["message"] = "Browser runtime is no longer available."
            session["updated_at"] = _utc_now()
            self._sessions[session_id] = session
            self._save_store()
            return session

        runtime = self._runtime[session_id]
        page = runtime["page"]
        viewport = page.viewport_size or {"width": 1440, "height": 960}
        actual_width = int(viewport.get("width") or 1440)
        actual_height = int(viewport.get("height") or 960)
        scale_x = actual_width / max(float(image_width or actual_width), 1.0)
        scale_y = actual_height / max(float(image_height or actual_height), 1.0)
        target_x = int(float(x) * scale_x)
        target_y = int(float(y) * scale_y)
        await page.mouse.click(target_x, target_y)
        await page.wait_for_timeout(800)
        return await self._refresh_session(session_id)

    async def drag(
        self,
        session_id: str,
        *,
        user_id: str,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
        image_width: float,
        image_height: float,
        steps: int = 18,
    ) -> Dict[str, Any]:
        session = self.peek_session(session_id, user_id=user_id)
        if not session:
            return {}
        if not self._runtime_alive(session_id):
            session["state"] = "expired"
            session["message"] = "Browser runtime is no longer available."
            session["updated_at"] = _utc_now()
            self._sessions[session_id] = session
            self._save_store()
            return session

        runtime = self._runtime[session_id]
        page = runtime["page"]
        viewport = page.viewport_size or {"width": 1440, "height": 960}
        actual_width = int(viewport.get("width") or 1440)
        actual_height = int(viewport.get("height") or 960)
        scale_x = actual_width / max(float(image_width or actual_width), 1.0)
        scale_y = actual_height / max(float(image_height or actual_height), 1.0)
        start_x = int(float(from_x) * scale_x)
        start_y = int(float(from_y) * scale_y)
        end_x = int(float(to_x) * scale_x)
        end_y = int(float(to_y) * scale_y)

        await page.mouse.move(start_x, start_y)
        await page.mouse.down()
        await page.mouse.move(end_x, end_y, steps=max(4, int(steps or 18)))
        await page.mouse.up()
        await page.wait_for_timeout(1200)
        session = await self._refresh_session(session_id)
        if session.get("state") in {"ready", "resumed"}:
            await self._persist_cookies(session_id)
        return session

    async def refresh(self, session_id: str, *, user_id: str) -> Dict[str, Any]:
        return await self.get_session(session_id, user_id=user_id)

    async def close(self, session_id: str, *, user_id: str) -> Dict[str, Any]:
        session = self.peek_session(session_id, user_id=user_id)
        if not session:
            return {}
        await self._close_runtime(session_id)
        session["state"] = "closed"
        session["message"] = "Challenge session closed."
        session["updated_at"] = _utc_now()
        self._sessions[session_id] = session
        self._save_store()
        return dict(session)
