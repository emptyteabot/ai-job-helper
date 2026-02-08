from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional

import requests

from .base import JobProvider, JobSearchParams


class JoobleProvider(JobProvider):
    """
    Real-time job search via Jooble API.

    Docs: https://jooble.org/api/about (API key required).
    """

    name = "jooble"

    def __init__(self, api_key: Optional[str] = None, timeout_s: int = 12):
        self.api_key = api_key or os.getenv("JOOBLE_API_KEY", "").strip()
        self.timeout_s = timeout_s
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _job_id(self, job: Dict[str, Any]) -> str:
        # Jooble returns an "id" but it's not always present. We create a stable
        # ID derived from link/title/company.
        raw = "|".join(
            [
                str(job.get("id", "")).strip(),
                str(job.get("link", "")).strip(),
                str(job.get("title", "")).strip(),
                str(job.get("company", "")).strip(),
            ]
        )
        return "jooble_" + hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def search_jobs(self, params: JobSearchParams) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise RuntimeError("JOOBLE_API_KEY 未配置，无法使用实时岗位数据源。")

        endpoint = f"https://jooble.org/api/{self.api_key}"

        # Jooble REST API parameters: keywords + optional location/salary/etc.
        # We'll keep location as a dedicated field (per docs) but still allow
        # extra qualifiers in keywords for better relevance.
        q_parts = [k.strip() for k in (params.keywords or []) if k and k.strip()]
        if params.experience:
            q_parts.append(params.experience.strip())
        query = " ".join(q_parts) if q_parts else "jobs"

        payload: Dict[str, Any] = {"keywords": query}
        if params.location:
            payload["location"] = params.location.strip()
        if params.salary_min:
            payload["salary"] = int(params.salary_min)

        try:
            resp = requests.post(endpoint, json=payload, timeout=self.timeout_s)
        except requests.RequestException as e:
            raise RuntimeError(f"Jooble API 请求失败: {e}") from e

        if resp.status_code != 200:
            # Jooble returns JSON error body sometimes; keep it short.
            raise RuntimeError(f"Jooble API 返回异常: HTTP {resp.status_code}")

        data = resp.json() if resp.content else {}
        jobs = data.get("jobs") or []

        out: List[Dict[str, Any]] = []
        for j in jobs[: max(1, int(params.limit or 50))]:
            job_id = self._job_id(j)
            job = {
                "id": job_id,
                "title": j.get("title") or "",
                "company": j.get("company") or "",
                "location": j.get("location") or "",
                "salary": j.get("salary") or "",
                "description": j.get("snippet") or j.get("description") or "",
                "requirements": [],
                "platform": j.get("source") or "Jooble",
                "link": j.get("link") or "",
                "updated": j.get("updated") or "",
                "provider": self.name,
            }
            self._cache[job_id] = job
            out.append(job)

        return out

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        # Jooble API doesn't provide a detail endpoint; we return cached entry
        # from the most recent search.
        return self._cache.get(job_id)
