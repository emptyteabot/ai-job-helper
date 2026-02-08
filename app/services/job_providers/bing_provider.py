from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from .base import JobProvider, JobSearchParams


class BingWebSearchProvider(JobProvider):
    """
    Real-time job link discovery via Bing Web Search API.

    This is not scraping job boards directly. It queries Bing and returns result URLs/snippets.

    Note: Microsoft announced Bing Search APIs retirement on 11 Aug 2025. If you
    don't already have an existing subscription, you likely can't obtain new keys.
    Prefer Jooble (JOOBLE_API_KEY) for real-time job search.

    Env:
      - BING_SEARCH_API_KEY: required
      - BING_SEARCH_ENDPOINT: optional, defaults to https://api.bing.microsoft.com/v7.0/search
      - JOB_SEARCH_SITES: optional comma-separated domains to restrict, e.g.
        "zhipin.com,liepin.com,zhaopin.com,51job.com"
    """

    name = "bing"

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, timeout_s: int = 12):
        self.api_key = (api_key or os.getenv("BING_SEARCH_API_KEY", "")).strip()
        self.endpoint = (endpoint or os.getenv("BING_SEARCH_ENDPOINT", "")).strip() or "https://api.bing.microsoft.com/v7.0/search"
        self.timeout_s = timeout_s
        self._cache: Dict[str, Dict[str, Any]] = {}

        sites = os.getenv("JOB_SEARCH_SITES", "").strip()
        self.sites = [s.strip().lstrip(".") for s in sites.split(",") if s.strip()] if sites else []

    def _job_id(self, url: str) -> str:
        return "bing_" + hashlib.sha1(url.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def _platform_from_url(self, url: str) -> str:
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            return "Bing"
        if "zhipin.com" in host:
            return "Boss直聘"
        if "liepin.com" in host:
            return "猎聘"
        if "zhaopin.com" in host:
            return "智联招聘"
        if "51job.com" in host:
            return "前程无忧"
        return host or "Bing"

    def search_jobs(self, params: JobSearchParams) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise RuntimeError("BING_SEARCH_API_KEY 未配置，无法使用实时搜索数据源。")

        q_parts: List[str] = []
        for k in (params.keywords or []):
            k = (k or "").strip()
            if k:
                q_parts.append(k)
        if params.location:
            q_parts.append(params.location.strip())
        # Add Chinese job intent term to improve relevance
        q_parts.append("招聘 OR 职位")

        q = " ".join(q_parts) if q_parts else "招聘"
        if self.sites:
            site_filter = " OR ".join([f"site:{d}" for d in self.sites])
            q = f"({q}) ({site_filter})"

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        query = {"q": q, "mkt": "zh-CN", "count": max(1, min(int(params.limit or 50), 50))}

        try:
            resp = requests.get(self.endpoint, headers=headers, params=query, timeout=self.timeout_s)
        except requests.RequestException as e:
            raise RuntimeError(f"Bing Search API 请求失败: {e}") from e

        if resp.status_code != 200:
            raise RuntimeError(f"Bing Search API 返回异常: HTTP {resp.status_code}")

        data = resp.json() if resp.content else {}
        items = (((data.get("webPages") or {}).get("value")) or [])

        out: List[Dict[str, Any]] = []
        for it in items:
            url = (it.get("url") or "").strip()
            if not url:
                continue
            job_id = self._job_id(url)

            job = {
                "id": job_id,
                "title": (it.get("name") or "").strip(),
                "company": "",  # unknown from search result reliably
                "location": params.location or "",
                "salary": "",
                "description": (it.get("snippet") or "").strip(),
                "requirements": [],
                "platform": self._platform_from_url(url),
                "link": url,
                "updated": "",
                "provider": self.name,
            }
            self._cache[job_id] = job
            out.append(job)

        return out

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(job_id)
