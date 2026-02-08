from __future__ import annotations

import hashlib
import html as html_lib
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlparse

import requests

from .base import JobProvider, JobSearchParams


class BaiduSearchProvider(JobProvider):
    """
    Real-time job link discovery via Baidu search result HTML.

    This is a pragmatic no-key approach for China market:
    - query Baidu
    - extract result titles + URLs
    - resolve Baidu redirect links to final URL

    Caveats:
    - Can be blocked by anti-bot / captcha at any time.
    - Do NOT use at high QPS.

    Env:
      - JOB_SEARCH_SITES: optional comma-separated domains to restrict
        e.g. "zhipin.com,liepin.com,zhaopin.com,51job.com"
      - BAIDU_TIMEOUT_S: optional, default 12
    """

    name = "baidu"

    def __init__(self, timeout_s: Optional[int] = None):
        self.timeout_s = int(timeout_s or os.getenv("BAIDU_TIMEOUT_S", "12") or "12")
        sites = os.getenv("JOB_SEARCH_SITES", "").strip()
        self.sites = [s.strip().lstrip(".") for s in sites.split(",") if s.strip()] if sites else []
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _job_id(self, url: str) -> str:
        return "baidu_" + hashlib.sha1(url.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def _platform_from_url(self, url: str) -> str:
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            return "百度"
        if "zhipin.com" in host:
            return "Boss直聘"
        if "liepin.com" in host:
            return "猎聘"
        if "zhaopin.com" in host:
            return "智联招聘"
        if "51job.com" in host:
            return "前程无忧"
        return host or "百度"

    def _resolve_redirect(self, url: str) -> str:
        # Baidu uses redirector links; follow once to get the final job board URL.
        try:
            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122"},
                timeout=self.timeout_s,
                allow_redirects=True,
            )
            return r.url or url
        except Exception:
            return url

    def search_jobs(self, params: JobSearchParams) -> List[Dict[str, Any]]:
        limit = max(1, min(int(params.limit or 50), 50))

        q_parts: List[str] = []
        for k in (params.keywords or []):
            k = (k or "").strip()
            if k:
                q_parts.append(k)
        if params.location:
            q_parts.append(params.location.strip())
        if params.experience:
            q_parts.append(params.experience.strip())
        q_parts.append("招聘 职位 投递")

        base_query = " ".join(q_parts) if q_parts else "招聘 职位"

        def fetch(query: str, n: int) -> List[tuple[str, str]]:
            wd = quote_plus(query)
            url = f"https://www.baidu.com/s?wd={wd}&rn={max(1, min(n, 50))}"
            resp = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
                timeout=self.timeout_s,
            )
            # Baidu may redirect to captcha page.
            if "wappass.baidu.com" in (resp.url or "") or "captcha" in (resp.url or ""):
                raise RuntimeError("百度触发安全验证/验证码，无法继续实时搜索。请稍后重试或改用第三方API。")
            text = resp.text or ""
            if ("安全验证" in text) or ("请输入验证码" in text):
                raise RuntimeError("百度触发安全验证/验证码，无法继续实时搜索。请稍后重试或改用本地数据/第三方API。")

            # Typical pattern: <h3 ...><a href="...">TITLE</a>
            pattern = re.compile(r"<h3[^>]*>\\s*<a\\s+[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.I | re.S)
            matches = pattern.findall(text)
            pairs: List[tuple[str, str]] = []
            for href, raw_title in matches:
                title = re.sub(r"<[^>]+>", "", raw_title)
                title = html_lib.unescape(title).strip()
                if href and title:
                    pairs.append((title, href))
            return pairs

        # Avoid complex OR queries; Baidu often changes markup/blocks them.
        # Instead, query each site separately and merge results.
        pairs: List[tuple[str, str]] = []
        if self.sites:
            per_site = max(3, limit // min(len(self.sites), 4))
            for site in self.sites[:4]:
                pairs.extend(fetch(f"{base_query} site:{site}", per_site))
                if len(pairs) >= limit:
                    break
        else:
            pairs = fetch(base_query, limit)

        out: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for title, href in pairs:
            if len(out) >= limit:
                break
            final_url = self._resolve_redirect(href)
            if final_url in seen:
                continue
            seen.add(final_url)

            job_id = self._job_id(final_url)
            job = {
                "id": job_id,
                "title": title,
                "company": "",
                "location": params.location or "",
                "salary": "",
                "description": "",
                "requirements": [],
                "platform": self._platform_from_url(final_url),
                "link": final_url,
                "updated": "",
                "provider": self.name,
            }
            self._cache[job_id] = job
            out.append(job)

        return out

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(job_id)
