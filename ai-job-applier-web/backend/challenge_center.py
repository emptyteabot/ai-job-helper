from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        self.store_file.write_text(json.dumps(self._sessions, ensure_ascii=False, indent=2), encoding="utf-8")

    async def _ensure_playwright(self):
        if self._playwright is not None:
            return self._playwright
        self._playwright = await async_playwright().start()
        return self._playwright

    async def _persist_cookies(self, session_id: str) -> None:
        session = self._sessions.get(session_id, {})
        cookie_file = str(session.get("cookie_file") or "").strip()
        runtime = self._runtime.get(session_id)
        if not cookie_file or not runtime:
            return
        try:
            cookies = await runtime["context"].cookies()
            target = Path(cookie_file)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            return

    async def _detect_challenge(self, page) -> tuple[str, str]:
        url = (page.url or "").lower()
        markers = ("验证码", "安全验证", "captcha", "verify", "human verification", "passport/zp/verify", "security.html")
        try:
            content = await page.content()
            lowered = content.lower()
        except Exception:
            lowered = ""
        if any(marker.lower() in lowered or marker.lower() in url for marker in markers):
            return "challenge_required", "检测到验证码或安全验证，等待人工接管。"
        return "ready", "页面可继续自动执行。"

    async def _snapshot(self, session_id: str) -> str:
        runtime = self._runtime.get(session_id)
        if not runtime:
            return ""
        snapshot_path = self.snapshot_dir / f"{session_id}.png"
        await runtime["page"].screenshot(path=str(snapshot_path), full_page=True)
        return str(snapshot_path)

    async def _refresh_session(self, session_id: str) -> Dict[str, Any]:
        runtime = self._runtime.get(session_id)
        if not runtime:
            session = self._sessions.get(session_id, {})
            session["message"] = session.get("message") or "运行时会话不存在。"
            self._sessions[session_id] = session
            self._save_store()
            return session

        page = runtime["page"]
        session = self._sessions.get(session_id, {})
        try:
            state, message = await self._detect_challenge(page)
        except Exception:
            state = str(session.get("state") or "checking")
            message = "页面正在跳转，暂时无法刷新挑战状态。"
        try:
            screenshot_path = await self._snapshot(session_id)
        except Exception:
            screenshot_path = str(session.get("screenshot_path") or "")
        session.update(
            {
                "id": session_id,
                "state": state,
                "message": message,
                "current_url": page.url,
                "screenshot_path": screenshot_path,
                "updated_at": _utc_now(),
            }
        )
        self._sessions[session_id] = session
        self._save_store()
        if session.get("state") in {"ready", "resumed"}:
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
        for existing_id, session in list(self._sessions.items()):
            if str(session.get("user_id") or "") != str(user_id or ""):
                continue
            if str(session.get("provider") or "") != str(provider or ""):
                continue
            if str(session.get("state") or "") == "closed":
                continue
            return await self.get_session(existing_id, user_id=str(user_id or ""))

        playwright = await self._ensure_playwright()
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2500)
        except Exception:
            try:
                await page.goto(url, wait_until="commit", timeout=15000)
                await page.wait_for_timeout(3000)
            except Exception:
                await page.wait_for_timeout(5000)

        session_id = uuid.uuid4().hex
        self._runtime[session_id] = {
            "browser": browser,
            "context": context,
            "page": page,
        }
        self._sessions[session_id] = {
            "id": session_id,
            "user_id": str(user_id or ""),
            "provider": provider,
            "title": title or "Challenge Session",
            "target_url": url,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "state": "checking",
            "message": "会话已创建，正在检测挑战状态。",
            "current_url": page.url,
            "screenshot_path": "",
            "cookie_file": cookie_file,
            "metadata": dict(metadata or {}),
        }
        self._save_store()
        return await self._refresh_session(session_id)

    def list_sessions(self, *, user_id: str) -> List[Dict[str, Any]]:
        rows = [dict(row) for row in self._sessions.values() if str(row.get("user_id") or "") == str(user_id or "")]
        rows.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
        return rows

    async def get_session(self, session_id: str, *, user_id: str) -> Dict[str, Any]:
        session = dict(self._sessions.get(str(session_id or ""), {}))
        if not session or str(session.get("user_id") or "") != str(user_id or ""):
            return {}
        if session_id in self._runtime:
            try:
                return await self._refresh_session(session_id)
            except Exception:
                return session
        return session

    def peek_session(self, session_id: str, *, user_id: str) -> Dict[str, Any]:
        session = dict(self._sessions.get(str(session_id or ""), {}))
        if not session or str(session.get("user_id") or "") != str(user_id or ""):
            return {}
        return session

    async def submit_code(self, session_id: str, *, user_id: str, code: str) -> Dict[str, Any]:
        session = await self.get_session(session_id, user_id=user_id)
        if not session:
            return {}
        runtime = self._runtime.get(session_id)
        if not runtime:
            session["message"] = "运行时浏览器会话不存在，无法继续提交验证码。"
            self._sessions[session_id] = session
            self._save_store()
            return session

        page = runtime["page"]
        locators = [
            "input[type='text']",
            "input[type='tel']",
            "input[type='number']",
            "input:not([type])",
            "textarea",
        ]
        filled = False
        for selector in locators:
            locator = page.locator(selector)
            count = await locator.count()
            for index in range(min(count, 5)):
                handle = locator.nth(index)
                if await handle.is_visible():
                    await handle.fill(str(code or ""))
                    filled = True
                    break
            if filled:
                break

        if not filled:
            session["state"] = "failed"
            session["message"] = "未找到可填写的验证码输入框。"
            self._sessions[session_id] = session
            self._save_store()
            return session

        button_selectors = [
            "button:has-text('提交')",
            "button:has-text('确定')",
            "button:has-text('验证')",
            "button:has-text('继续')",
            "button:has-text('Submit')",
            "button:has-text('Verify')",
        ]
        clicked = False
        for selector in button_selectors:
            locator = page.locator(selector)
            count = await locator.count()
            if count and await locator.first.is_visible():
                await locator.first.click()
                clicked = True
                break
        if not clicked:
            await page.keyboard.press("Enter")

        await page.wait_for_timeout(1200)
        session = await self._refresh_session(session_id)
        if session.get("state") != "challenge_required":
            session["state"] = "resumed"
            session["message"] = "验证码已提交，浏览器会话已恢复。"
            self._sessions[session_id] = session
            self._save_store()
        return session

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
        runtime = self._runtime.get(session_id)
        if not runtime:
            session["message"] = "运行时浏览器会话不存在，无法继续点击。"
            self._sessions[session_id] = session
            self._save_store()
            return session
        viewport = runtime["page"].viewport_size or {"width": 1440, "height": 960}
        actual_width = int(viewport.get("width") or 1440)
        actual_height = int(viewport.get("height") or 960)

        scale_x = actual_width / max(float(image_width or actual_width), 1.0)
        scale_y = actual_height / max(float(image_height or actual_height), 1.0)
        target_x = int(float(x) * scale_x)
        target_y = int(float(y) * scale_y)
        await runtime["page"].mouse.click(target_x, target_y)
        await runtime["page"].wait_for_timeout(800)
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
        runtime = self._runtime.get(session_id)
        if not runtime:
            session["message"] = "运行时浏览器会话不存在，无法继续拖拽。"
            self._sessions[session_id] = session
            self._save_store()
            return session
        viewport = runtime["page"].viewport_size or {"width": 1440, "height": 960}
        actual_width = int(viewport.get("width") or 1440)
        actual_height = int(viewport.get("height") or 960)

        scale_x = actual_width / max(float(image_width or actual_width), 1.0)
        scale_y = actual_height / max(float(image_height or actual_height), 1.0)
        start_x = int(float(from_x) * scale_x)
        start_y = int(float(from_y) * scale_y)
        end_x = int(float(to_x) * scale_x)
        end_y = int(float(to_y) * scale_y)

        page = runtime["page"]
        await page.mouse.move(start_x, start_y)
        await page.mouse.down()
        await page.mouse.move(end_x, end_y, steps=max(4, int(steps or 18)))
        await page.mouse.up()
        await page.wait_for_timeout(1200)
        return await self._refresh_session(session_id)

    async def refresh(self, session_id: str, *, user_id: str) -> Dict[str, Any]:
        return await self.get_session(session_id, user_id=user_id)

    async def close(self, session_id: str, *, user_id: str) -> Dict[str, Any]:
        session = self.peek_session(session_id, user_id=user_id)
        if not session:
            return {}
        runtime = self._runtime.pop(session_id, None)
        if runtime:
            try:
                await runtime["context"].close()
            except Exception:
                pass
            try:
                await runtime["browser"].close()
            except Exception:
                pass
        session["state"] = "closed"
        session["message"] = "会话已关闭。"
        session["updated_at"] = _utc_now()
        self._sessions[session_id] = session
        self._save_store()
        return dict(session)
