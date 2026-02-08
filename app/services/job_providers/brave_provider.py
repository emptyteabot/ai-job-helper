from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from .base import JobProvider, JobSearchParams


class BraveSearchProvider(JobProvider):
    """
    Real-time job link discovery via Brave Search API (legit web search API).

    Docs show:
      GET https://api.search.brave.com/res/v1/web/search
      Header: X-Subscription-Token: <BRAVE_SEARCH_API_KEY>

    Env:
      - BRAVE_SEARCH_API_KEY: required
      - BRAVE_SEARCH_COUNTRY: optional, default "cn"
      - BRAVE_SEARCH_LANG: optional, default "zh-hans"
      - JOB_SEARCH_SITES: optional comma-separated domains to restrict
        e.g. "zhipin.com,liepin.com,zhaopin.com,51job.com"
    """

    name = "brave"

    def __init__(self, api_key: Optional[str] = None, timeout_s: int = 12):
        self.api_key = (api_key or os.getenv("BRAVE_SEARCH_API_KEY", "")).strip()
        self.timeout_s = timeout_s
        self.country = (os.getenv("BRAVE_SEARCH_COUNTRY", "cn") or "cn").strip().lower()
        self.lang = (os.getenv("BRAVE_SEARCH_LANG", "zh-hans") or "zh-hans").strip().lower()

        sites = os.getenv("JOB_SEARCH_SITES", "").strip()
        self.sites = [s.strip().lstrip(".") for s in sites.split(",") if s.strip()] if sites else []
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _job_id(self, url: str) -> str:
        return "brave_" + hashlib.sha1(url.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def _platform_from_url(self, url: str) -> str:
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            return "Brave"
        if "zhipin.com" in host:
            return "Boss直聘"
        if "liepin.com" in host:
            return "猎聘"
        if "zhaopin.com" in host:
            return "智联招聘"
        if "51job.com" in host:
            return "前程无忧"
        return host or "Brave"

    def search_jobs(self, params: JobSearchParams) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise RuntimeError("BRAVE_SEARCH_API_KEY 未配置，无法使用实时搜索数据源。")

        limit = max(1, min(int(params.limit or 50), 20))  # Brave example uses count; keep conservative

        q_parts: List[str] = []
        for k in (params.keywords or []):
            k = (k or "").strip()
            if k:
                q_parts.append(k)
        if params.location:
            q_parts.append(params.location.strip())
        if params.experience:
            q_parts.append(params.experience.strip())
        q_parts.append("招聘 OR 职位")
        q = " ".join(q_parts) if q_parts else "招聘 职位"

        if self.sites:
            site_filter = " OR ".join([f"site:{d}" for d in self.sites])
            q = f"({q}) ({site_filter})"

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"Accept": "application/json", "X-Subscription-Token": self.api_key}
        query: Dict[str, Any] = {
            "q": q,
            "count": limit,
            "country": self.country,
            "search_lang": self.lang,
        }

        try:
            resp = requests.get(url, headers=headers, params=query, timeout=self.timeout_s)
        except requests.RequestException as e:
            raise RuntimeError(f"Brave Search API 请求失败: {e}") from e

        if resp.status_code != 200:
            raise RuntimeError(f"Brave Search API 返回异常: HTTP {resp.status_code}")

        data = resp.json() if resp.content else {}
        results = (((data.get("web") or {}).get("results")) or [])

        out: List[Dict[str, Any]] = []
        for it in results:
            link = (it.get("url") or "").strip()
            if not link:
                continue
            job_id = self._job_id(link)
            job = {
                "id": job_id,
                "title": (it.get("title") or "").strip(),
                "company": "",
                "location": params.location or "",
                "salary": "",
                "description": (it.get("description") or "").strip(),
                "requirements": [],
                "platform": self._platform_from_url(link),
                "link": link,
                "updated": "",
                "provider": self.name,
            }
            self._cache[job_id] = job
            out.append(job)

        return out

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(job_id)

