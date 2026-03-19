from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .base_applier import BaseApplier

logger = logging.getLogger(__name__)


class BossApplier(BaseApplier):
    """Boss 直聘自动投递器（安全可控版）。

    Notes:
    - 不做验证码绕过。
    - 默认在验证码/短信码环节等待人工完成，然后继续自动化流程。
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.base_url = "https://www.zhipin.com"
        self.login_url = "https://login.zhipin.com/"
        self.jobs_url = "https://www.zhipin.com/web/geek/job"

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        ]

    async def _init_browser(self) -> bool:
        try:
            if self.page:
                return True

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=bool(self.config.get("headless", False)),
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            self.context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={"width": 1440, "height": 900},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )
            self.page = await self.context.new_page()
            return True
        except Exception as e:
            logger.error("Boss 浏览器初始化失败: %s", e)
            return False

    async def _random_delay(self, min_s: float = 0.3, max_s: float = 1.1) -> None:
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def _first_selector(self, selectors: List[str]) -> Optional[Any]:
        for sel in selectors:
            try:
                el = await self.page.query_selector(sel)
                if el:
                    return el
            except Exception:
                continue
        return None

    async def _wait_captcha_done(self) -> bool:
        mode = str(self.config.get("captcha_mode", "manual") or "manual").strip().lower()
        wait_s = int(self.config.get("captcha_wait_timeout", 180) or 180)
        started = time.time()

        slider_selectors = [
            ".geetest_slider_button",
            ".yidun_slider",
            "[class*='captcha']",
            "[class*='verify']",
        ]

        has_captcha = False
        for sel in slider_selectors:
            try:
                if await self.page.query_selector(sel):
                    has_captcha = True
                    break
            except Exception:
                pass

        if not has_captcha:
            return True

        if mode in {"abort", "fail_fast", "strict"}:
            logger.error("检测到验证码，当前 captcha_mode=%s，终止自动流程。", mode)
            return False

        logger.warning("检测到验证码，请在浏览器中手动完成，系统等待继续。")

        while time.time() - started < wait_s:
            still_blocked = False
            for sel in slider_selectors:
                try:
                    if await self.page.query_selector(sel):
                        still_blocked = True
                        break
                except Exception:
                    pass
            if not still_blocked:
                return True
            await asyncio.sleep(1.0)

        return False

    async def _wait_login_done(self) -> bool:
        wait_s = int(self.config.get("login_wait_timeout", 240) or 240)
        started = time.time()
        while time.time() - started < wait_s:
            try:
                url = self.page.url or ""
            except Exception:
                url = ""

            if "login.zhipin.com" not in url and "zhipin.com" in url:
                return True

            signed_selectors = [
                "a[href*='/web/geek/job']",
                "[class*='header'] [class*='name']",
                "[class*='user']",
            ]
            for sel in signed_selectors:
                try:
                    if await self.page.query_selector(sel):
                        return True
                except Exception:
                    pass

            await asyncio.sleep(1.0)

        return False

    def login(self, phone: str, password: str = None) -> bool:
        return asyncio.run(self._async_login(phone))

    async def _async_login(self, phone: str) -> bool:
        if not phone or not str(phone).strip():
            logger.error("Boss 登录失败：手机号为空")
            return False

        if not await self._init_browser():
            return False

        try:
            await self.page.goto(self.login_url, wait_until="domcontentloaded", timeout=45000)
            await self._random_delay(0.6, 1.4)

            tab = await self._first_selector([
                "text=手机号登录",
                "text=手机登录",
                "[ka='header-login-phone']",
            ])
            if tab:
                try:
                    await tab.click()
                    await self._random_delay(0.3, 0.8)
                except Exception:
                    pass

            phone_input = await self._first_selector([
                "input[placeholder*='手机号']",
                "input[type='tel']",
                "input[name*='phone']",
            ])
            if not phone_input:
                logger.error("Boss 登录失败：未找到手机号输入框")
                return False

            await phone_input.click()
            await phone_input.fill("")
            await phone_input.type(str(phone).strip(), delay=random.randint(40, 110))

            send_btn = await self._first_selector([
                "button:has-text('获取验证码')",
                "button:has-text('发送验证码')",
                "a:has-text('获取验证码')",
            ])
            if send_btn:
                await send_btn.click()

            if not await self._wait_captcha_done():
                logger.error("Boss 登录失败：验证码等待超时")
                return False

            logger.info("请在浏览器输入短信验证码并完成登录，系统等待中...")
            if not await self._wait_login_done():
                logger.error("Boss 登录失败：登录等待超时")
                return False

            logger.info("Boss 登录成功")
            return True
        except Exception as e:
            logger.exception("Boss 登录异常: %s", e)
            return False

    def search_jobs(self, keywords: str, location: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return asyncio.run(self._async_search_jobs(keywords, location, filters))

    async def _async_search_jobs(self, keywords: str, location: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not await self._init_browser():
            return []

        q = quote_plus((keywords or "").strip() or "Python")
        city = quote_plus((location or "").strip())
        url = f"{self.jobs_url}?query={q}"
        if city:
            url += f"&city={city}"

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await self._random_delay(1.0, 2.0)

            items = await self.page.evaluate(
                """
                () => {
                  const out = [];
                  const seen = new Set();
                  const anchors = Array.from(document.querySelectorAll('a[href]'));
                  for (const a of anchors) {
                    const href = (a.href || '').trim();
                    const text = (a.innerText || a.textContent || '').trim();
                    if (!href || href.indexOf('/job_detail/') < 0) continue;
                    if (seen.has(href)) continue;
                    seen.add(href);
                    out.push({ href, text });
                    if (out.length >= 120) break;
                  }
                  return out;
                }
                """
            )

            out: List[Dict[str, Any]] = []
            for idx, row in enumerate(items or [], 1):
                href = str((row or {}).get("href") or "").strip()
                if not href:
                    continue
                title = str((row or {}).get("text") or "").strip() or f"Boss岗位 {idx}"
                out.append(
                    {
                        "id": f"boss_{idx}_{abs(hash(href))}",
                        "title": title,
                        "company": "",
                        "location": location or "",
                        "salary": "",
                        "platform": "boss",
                        "link": href,
                        "provider": "boss_applier",
                    }
                )

            # 去重 + 限制
            dedup: List[Dict[str, Any]] = []
            seen_links = set()
            for j in out:
                link = j.get("link")
                if link in seen_links:
                    continue
                seen_links.add(link)
                dedup.append(j)

            limit = int(self.config.get("max_apply_per_session", 50) or 50)
            return dedup[: max(1, min(limit, 100))]
        except Exception as e:
            logger.exception("Boss 搜索岗位失败: %s", e)
            return []

    def apply_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self._async_apply_job(job))

    async def _async_apply_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        link = str((job or {}).get("link") or "").strip()
        title = str((job or {}).get("title") or "未知岗位")
        if not link:
            return {"success": False, "message": "岗位缺少链接", "job": job}

        if not await self._init_browser():
            return {"success": False, "message": "浏览器初始化失败", "job": job}

        try:
            await self.page.goto(link, wait_until="domcontentloaded", timeout=45000)
            await self._random_delay(0.6, 1.6)

            btn = await self._first_selector([
                "button:has-text('立即沟通')",
                "button:has-text('立即投递')",
                "button:has-text('沟通')",
                "a:has-text('立即沟通')",
            ])
            if not btn:
                return {"success": False, "message": "未找到投递按钮", "job": job}

            await btn.click()
            await self._random_delay(0.8, 1.5)
            return {"success": True, "message": f"投递动作已执行: {title}", "job": job}
        except Exception as e:
            logger.exception("Boss 投递失败: %s", e)
            return {"success": False, "message": str(e), "job": job}

    def run_apply_pipeline(
        self,
        keywords: str = "",
        location: str = "",
        jobs: Optional[List[Dict[str, Any]]] = None,
        max_count: Optional[int] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ):
        """兼容旧版运行时入口。

        说明:
        - 在同步上下文中返回最终 dict 结果。
        - 在已有事件循环中返回 coroutine，供 `await` 调用。
        """
        coro = self._async_run_apply_pipeline(
            keywords=keywords,
            location=location,
            jobs=jobs,
            max_count=max_count,
            user_profile=user_profile,
            filters=filters,
        )
        try:
            asyncio.get_running_loop()
            return coro
        except RuntimeError:
            return asyncio.run(coro)

    async def _async_run_apply_pipeline(
        self,
        keywords: str = "",
        location: str = "",
        jobs: Optional[List[Dict[str, Any]]] = None,
        max_count: Optional[int] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        local_user_profile = user_profile or {}
        config_user_profile = self.config.get("user_profile") or {}
        merged_user_profile = {**config_user_profile, **local_user_profile}

        phone = str(
            merged_user_profile.get("phone")
            or self.config.get("phone")
            or ""
        ).strip()
        if not phone:
            return {
                "success": False,
                "message": "Boss 自动投递需要手机号：user_profile.phone",
                "total_attempted": 0,
                "applied": 0,
                "failed": 0,
                "results": [],
            }

        login_ok = await self._async_login(phone)
        if not login_ok:
            return {
                "success": False,
                "message": "Boss 登录失败",
                "total_attempted": 0,
                "applied": 0,
                "failed": 0,
                "results": [],
            }

        selected_jobs = list(jobs or [])
        if not selected_jobs:
            selected_jobs = await self._async_search_jobs(
                keywords or str(self.config.get("keywords") or ""),
                location or str(self.config.get("location") or ""),
                filters or {},
            )

        limit = int(max_count or self.config.get("max_apply_per_session") or 50)
        selected_jobs = selected_jobs[: max(1, limit)]

        applied = 0
        failed = 0
        results: List[Dict[str, Any]] = []

        for one_job in selected_jobs:
            one_result = await self._async_apply_job(one_job)
            if one_result.get("success"):
                applied += 1
            else:
                failed += 1
            results.append(one_result)

        return {
            "success": failed == 0 or applied > 0,
            "message": "Boss 自动投递流程执行完成",
            "total_attempted": len(results),
            "applied": applied,
            "failed": failed,
            "success_rate": (applied / len(results)) if results else 0,
            "results": results,
        }

    def cleanup(self):
        try:
            if self.context:
                asyncio.run(self.context.close())
        except Exception:
            pass
        try:
            if self.browser:
                asyncio.run(self.browser.close())
        except Exception:
            pass
        try:
            if self.playwright:
                asyncio.run(self.playwright.stop())
        except Exception:
            pass

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
