from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List


DESKTOP_BACKEND_DIR = Path(__file__).resolve().parents[2] / "ai-job-applier-desktop" / "backend"
if str(DESKTOP_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(DESKTOP_BACKEND_DIR))

try:
    from ai.boss_auto_apply import BossAutoApply
except Exception:  # pragma: no cover - optional dependency path
    BossAutoApply = None


class BossBridge:
    """
    Assisted Boss bridge.

    Scope:
    - launch browser and wait for user QR-code login
    - search real Boss jobs
    - run assisted batch apply

    Explicitly out of scope:
    - captcha bypass
    - SMS bypass
    - hidden browser anti-detection promises
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

    def available(self) -> bool:
        return self._client is not None

    def status(self) -> Dict[str, Any]:
        return {
            "available": self.available(),
            "assisted_only": True,
            "logged_in": bool(self._client and self._client.is_logged_in),
            "state": self._state,
            "message": self._last_message,
        }

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
        await self._client.init_browser()
        return await self._client.login_with_qrcode()

    def search_jobs(self, keyword: str, city: str, limit: int = 10) -> Dict[str, Any]:
        if not self._client:
            return {"success": False, "jobs": [], "message": "bridge unavailable"}
        jobs = asyncio.run(self._client.search_jobs(keyword=keyword, city=city))
        if jobs:
            self._state = "ready"
            self._last_message = "Boss search completed via assisted browser automation."
        else:
            self._state = "challenge_required"
            self._last_message = "Boss search returned no jobs. Browser session may still be blocked on captcha or verification."
        return {
            "success": bool(jobs),
            "assisted_only": True,
            "state": self._state,
            "jobs": jobs[: max(1, min(int(limit or 10), 50))],
            "message": self._last_message,
        }

    def batch_apply(
        self,
        keyword: str,
        city: str,
        max_count: int,
        greeting_template: str = "",
    ) -> Dict[str, Any]:
        if not self._client:
            return {"success": False, "message": "bridge unavailable"}
        self._state = "waiting_human"
        self._last_message = "Boss assisted apply started. If the browser hits QR-code or captcha, complete it and the run can continue."
        result = asyncio.run(
            self._client.batch_apply(
                keyword=keyword,
                city=city,
                max_count=max_count,
                greeting_template=greeting_template,
            )
        )
        if result.get("success", 0):
            self._state = "resumed"
            self._last_message = "Boss assisted apply completed after human-supervised checkpoints."
        else:
            self._state = "challenge_required"
            self._last_message = "Boss assisted apply did not complete. Human captcha or verification may still be required."
        result["assisted_only"] = True
        result["state"] = self._state
        result["message"] = self._last_message
        return result
