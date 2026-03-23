from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Optional


DESKTOP_BACKEND_DIR = Path(__file__).resolve().parents[2] / "ai-job-applier-desktop" / "backend"
if str(DESKTOP_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(DESKTOP_BACKEND_DIR))

try:
    from ai.boss_auto_apply import BossAutoApply
except Exception:  # pragma: no cover
    BossAutoApply = None


class BossBridge:
    """
    Assisted Boss bridge.

    This bridge does not bypass captcha. Its only job is to keep a real browser
    session alive, surface human checkpoints, and resume from the same runtime
    when possible.
    """

    def __init__(self) -> None:
        self._client = BossAutoApply() if BossAutoApply is not None else None
        if self._client is not None:
            self._client.cookies_file = Path(__file__).resolve().parent.parent / "data" / "boss_cookies.json"
        self._state = "ready" if self._client is not None else "unavailable"
        self._last_message = (
            "Boss bridge ready; QR-code login and captcha still require human completion."
            if self._client is not None
            else "Boss bridge unavailable because desktop automation dependencies are missing."
        )
        self._active_runtime_session: str = ""

    def available(self) -> bool:
        return self._client is not None

    def status(self) -> Dict[str, Any]:
        return {
            "available": self.available(),
            "assisted_only": True,
            "logged_in": bool(self._client and self._client.is_logged_in),
            "state": self._state,
            "message": self._last_message,
            "active_runtime_session": self._active_runtime_session or None,
        }

    async def _ensure_client(self) -> BossAutoApply:
        if not self._client:
            raise RuntimeError("bridge unavailable")
        return self._client

    def _decorate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(result or {})
        payload["assisted_only"] = True
        payload["state"] = self._state
        payload["message"] = self._last_message
        if self._active_runtime_session:
            payload["runtime_session_id"] = self._active_runtime_session
        return payload

    def _set_state_from_apply_result(self, result: Dict[str, Any]) -> None:
        checkpoint = bool(result.get("checkpoint_required")) or str(result.get("state") or "").strip().lower() in {
            "challenge_required",
            "waiting_human",
        }
        success_count = int(result.get("success", 0) or 0)
        failed_count = int(result.get("failed", 0) or 0)

        if checkpoint:
            self._state = "challenge_required"
            self._last_message = "Boss apply hit a human checkpoint. Complete verification and resume on the same session."
            return

        if success_count > 0:
            self._state = "resumed"
            self._last_message = "Boss assisted apply finished on the current browser session."
            self._active_runtime_session = ""
            return

        if failed_count > 0:
            self._state = "failed"
            self._last_message = "Boss apply completed without successes."
            self._active_runtime_session = ""
            return

        self._state = "ready"
        self._last_message = "Boss worker is ready."

    async def batch_apply_async(
        self,
        keyword: str,
        city: str,
        max_count: int,
        greeting_template: str = "",
        runtime: Optional[Dict[str, Any]] = None,
        runtime_session_id: str = "",
    ) -> Dict[str, Any]:
        client = await self._ensure_client()

        if runtime:
            candidate_id = str(runtime_session_id or "").strip()
            if self._active_runtime_session and candidate_id and self._active_runtime_session != candidate_id:
                self._state = "waiting_human"
                self._last_message = "Another Boss runtime session is already active."
                return self._decorate_result(
                    {
                        "success": 0,
                        "failed": 0,
                        "details": [],
                        "checkpoint_required": True,
                        "busy": True,
                    }
                )
            if candidate_id:
                self._active_runtime_session = candidate_id
            client.bind_runtime(
                page=runtime["page"],
                context=runtime.get("context"),
                owns_runtime=False,
            )

        self._state = "waiting_human"
        self._last_message = "Boss assisted apply started. Human checkpoints will pause and wait for confirmation."
        result = await client.batch_apply(
            keyword=keyword,
            city=city,
            max_count=max_count,
            greeting_template=greeting_template,
            reuse_existing_session=bool(runtime),
        )
        self._set_state_from_apply_result(result)
        return self._decorate_result(result)

    def batch_apply(
        self,
        keyword: str,
        city: str,
        max_count: int,
        greeting_template: str = "",
    ) -> Dict[str, Any]:
        if not self._client:
            return {"success": False, "message": "bridge unavailable"}
        return asyncio.run(self.batch_apply_async(keyword, city, max_count, greeting_template))

    def login(self) -> Dict[str, Any]:
        if not self._client:
            return self.status()
        self._state = "waiting_human"
        self._last_message = "Boss login launched. Complete QR-code or captcha in the browser, then the session can resume."
        success = asyncio.run(self._login())
        if success:
            self._state = "resumed"
            self._last_message = "Boss login completed after human confirmation."
        else:
            self._state = "challenge_required"
            self._last_message = "Boss login is blocked on QR-code or captcha. Human confirmation is still required."
        return {
            "success": success,
            "assisted_only": True,
            "state": self._state,
            "message": self._last_message,
        }

    async def _login(self) -> bool:
        client = await self._ensure_client()
        await client.init_browser()
        return await client.login_with_qrcode()

    def search_jobs(self, keyword: str, city: str, limit: int = 10) -> Dict[str, Any]:
        if not self._client:
            return {"success": False, "jobs": [], "message": "bridge unavailable"}
        jobs = asyncio.run(self._search_jobs(keyword, city))
        if jobs:
            self._state = "ready"
            self._last_message = "Boss search completed via assisted browser automation."
        else:
            self._state = "challenge_required"
            self._last_message = "Boss search returned no jobs. Browser session may still be blocked on challenge."
        return {
            "success": bool(jobs),
            "assisted_only": True,
            "state": self._state,
            "jobs": jobs[: max(1, min(int(limit or 10), 50))],
            "message": self._last_message,
        }

    async def _search_jobs(self, keyword: str, city: str):
        client = await self._ensure_client()
        if not await client._page_alive():
            await client.init_browser()
        return await client.search_jobs(keyword=keyword, city=city)
