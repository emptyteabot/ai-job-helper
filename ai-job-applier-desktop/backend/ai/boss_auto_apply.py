"""Boss direct-apply automation using Playwright."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

logger = logging.getLogger(__name__)

_HUMAN_CHECKPOINT_MARKERS = (
    "captcha",
    "verify",
    "challenge",
    "security",
    "passport/zp/verify",
    "security.html",
    "human verification",
    "验证码",
    "安全验证",
    "滑块",
)


class BossAutoApply:
    """Boss automation client with optional external runtime binding."""

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cookies_file = Path("data/boss_cookies.json")
        self.is_logged_in = False
        self._owns_runtime = True

    async def _page_alive(self) -> bool:
        if self.page is None:
            return False
        try:
            return not self.page.is_closed()
        except Exception:
            return False

    async def _load_cookies(self) -> None:
        if self.context is None or not self.cookies_file.exists():
            return
        try:
            cookies = json.loads(self.cookies_file.read_text(encoding="utf-8") or "[]")
        except Exception:
            return
        if not isinstance(cookies, list) or not cookies:
            return
        try:
            await self.context.add_cookies(cookies)
            self.is_logged_in = True
            logger.info("Loaded Boss cookies from %s", self.cookies_file)
        except Exception:
            return

    async def _persist_cookies(self) -> None:
        context = self.context
        if context is None:
            return
        try:
            cookies = await context.cookies()
            self.cookies_file.parent.mkdir(parents=True, exist_ok=True)
            self.cookies_file.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            return

    async def _human_checkpoint_detected(self) -> bool:
        if not await self._page_alive():
            return True
        page = self.page
        assert page is not None

        url = str(page.url or "").lower()
        text_parts = [url]
        try:
            text_parts.append((await page.title()).lower())
        except Exception:
            pass
        try:
            text_parts.append((await page.content()).lower())
        except Exception:
            pass
        haystack = " ".join(text_parts)
        return any(marker.lower() in haystack for marker in _HUMAN_CHECKPOINT_MARKERS)

    def bind_runtime(
        self,
        *,
        page: Page,
        context: Optional[BrowserContext] = None,
        owns_runtime: bool = False,
    ) -> None:
        """Bind to an externally managed Playwright runtime."""
        self.page = page
        self.context = context or page.context
        self._owns_runtime = bool(owns_runtime)
        self.is_logged_in = True

    async def init_browser(self):
        """Initialize a dedicated browser runtime."""
        if await self._page_alive():
            return

        if self.playwright is None:
            self.playwright = await async_playwright().start()
        if self.browser is None or not self.browser.is_connected():
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=["--start-maximized"],
            )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        self.page = await self.context.new_page()
        self._owns_runtime = True
        await self._load_cookies()

    async def login_with_qrcode(self):
        """Login to Boss via QR code, keeping runtime alive for follow-up actions."""
        try:
            if not await self._page_alive():
                await self.init_browser()
            page = self.page
            assert page is not None
            await page.goto("https://www.zhipin.com/")
            await page.wait_for_timeout(2000)

            login_btn = await page.query_selector(".btns .btn-sign-up")
            if login_btn:
                await login_btn.click()
                await page.wait_for_timeout(1000)

            qr_tab = await page.query_selector(".sign-form-switch")
            if qr_tab:
                await qr_tab.click()

            logger.info("Waiting for Boss QR login confirmation...")
            await page.wait_for_selector(".user-avatar", timeout=120000)
            await self._persist_cookies()
            self.is_logged_in = True
            logger.info("Boss login completed.")
            return True
        except Exception as exc:
            logger.error("Boss login failed: %s", exc)
            return False

    async def search_jobs(self, keyword: str, city: str = "全国", page_num: int = 1) -> List[Dict]:
        """Search jobs on Boss using the current runtime page."""
        if not await self._page_alive():
            return []

        page = self.page
        assert page is not None
        try:
            search_url = (
                "https://www.zhipin.com/web/geek/job?"
                f"query={quote_plus(str(keyword or '').strip())}&"
                f"city={quote_plus(str(city or '全国').strip())}&"
                f"page={max(1, int(page_num or 1))}"
            )
            await page.goto(search_url)
            await page.wait_for_timeout(3000)

            jobs: List[Dict[str, Any]] = []
            job_cards = await page.query_selector_all(".job-card-wrapper")
            for card in job_cards:
                try:
                    title_elem = await card.query_selector(".job-title")
                    salary_elem = await card.query_selector(".salary")
                    company_elem = await card.query_selector(".company-name")
                    link_elem = await card.query_selector(".job-card-left")

                    title = (await title_elem.inner_text()) if title_elem else ""
                    salary = (await salary_elem.inner_text()) if salary_elem else ""
                    company = (await company_elem.inner_text()) if company_elem else ""
                    job_link = (await link_elem.get_attribute("href")) if link_elem else ""
                    if job_link and not job_link.startswith("http"):
                        job_link = f"https://www.zhipin.com{job_link}"
                    jobs.append(
                        {
                            "title": str(title or "").strip(),
                            "salary": str(salary or "").strip(),
                            "company": str(company or "").strip(),
                            "url": str(job_link or "").strip(),
                            "platform": "boss",
                        }
                    )
                except Exception as exc:
                    logger.warning("Failed to parse one Boss job card: %s", exc)
                    continue
            logger.info("Boss search returned %s jobs", len(jobs))
            return jobs
        except Exception as exc:
            logger.error("Boss search failed: %s", exc)
            return []

    async def apply_job(self, job_url: str, greeting_message: str = "") -> bool:
        """Apply to one Boss job detail page using current runtime page."""
        if not await self._page_alive():
            return False
        page = self.page
        assert page is not None

        try:
            await page.goto(str(job_url or "").strip())
            await page.wait_for_timeout(2000)
            chat_btn = await page.query_selector(".btn-startchat")
            if not chat_btn:
                return False
            await chat_btn.click()
            await page.wait_for_timeout(2000)

            message = str(greeting_message or "").strip()
            if message:
                input_box = await page.query_selector(".chat-input")
                if input_box:
                    await input_box.fill(message)
                    await page.wait_for_timeout(500)
                    send_btn = await page.query_selector(".btn-send")
                    if send_btn:
                        await send_btn.click()
                        await page.wait_for_timeout(1000)
            return True
        except Exception as exc:
            logger.error("Boss apply failed for %s: %s", job_url, exc)
            return False

    async def batch_apply(
        self,
        keyword: str,
        city: str = "全国",
        max_count: int = 10,
        greeting_template: str = "",
        progress_callback=None,
        reuse_existing_session: bool = False,
    ) -> Dict:
        """Batch apply in one worker runtime."""
        try:
            if not await self._page_alive():
                await self.init_browser()

            if not self.is_logged_in and not reuse_existing_session:
                success = await self.login_with_qrcode()
                if not success:
                    return {"success": 0, "failed": 0, "details": [], "checkpoint_required": True, "message": "login failed"}

            if await self._human_checkpoint_detected():
                return {
                    "success": 0,
                    "failed": 0,
                    "details": [],
                    "checkpoint_required": True,
                    "message": "human verification is still required",
                }

            results: Dict[str, Any] = {"success": 0, "failed": 0, "details": []}
            jobs = await self.search_jobs(keyword, city)
            jobs = jobs[: max(1, int(max_count or 10))]
            if not jobs and await self._human_checkpoint_detected():
                return {
                    "success": 0,
                    "failed": 0,
                    "details": [],
                    "checkpoint_required": True,
                    "message": "challenge or verification blocked job list",
                }

            for index, job in enumerate(jobs, 1):
                if progress_callback:
                    progress_callback(index, len(jobs), f"applying {job.get('title', '')}")
                greeting = (
                    greeting_template.format(company=job.get("company", ""), position=job.get("title", ""))
                    if greeting_template
                    else f"您好，我对{job.get('title', '')}职位很感兴趣，期待与您沟通。"
                )
                success = await self.apply_job(str(job.get("url") or ""), greeting)
                if success:
                    results["success"] += 1
                    status = "success"
                else:
                    results["failed"] += 1
                    status = "failed"
                results["details"].append(
                    {
                        "job": job.get("title", ""),
                        "company": job.get("company", ""),
                        "status": status,
                    }
                )
                await asyncio.sleep(5)

            await self._persist_cookies()
            results["checkpoint_required"] = False
            return results
        except Exception as exc:
            logger.error("Boss batch apply failed: %s", exc)
            return {"success": 0, "failed": 0, "details": [], "message": str(exc), "checkpoint_required": True}

    async def close(self):
        """Close only runtimes owned by this client."""
        if not self._owns_runtime:
            self.page = None
            self.context = None
            self.browser = None
            self.is_logged_in = False
            return

        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self.is_logged_in = False


_boss_auto_apply = None


async def get_boss_auto_apply() -> BossAutoApply:
    """Return singleton Boss automation client."""
    global _boss_auto_apply
    if _boss_auto_apply is None:
        _boss_auto_apply = BossAutoApply()
        await _boss_auto_apply.init_browser()
    return _boss_auto_apply
