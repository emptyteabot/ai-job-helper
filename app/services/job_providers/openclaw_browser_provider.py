from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from .base import JobProvider, JobSearchParams


class _OpenClawError(RuntimeError):
    pass


@dataclass
class _CmdResult:
    code: int
    stdout: str
    stderr: str


def _run(cmd: List[str], timeout_s: int = 60) -> _CmdResult:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, shell=False)
    return _CmdResult(p.returncode, p.stdout or "", p.stderr or "")


def _extract_json(text: str) -> Any:
    # OpenClaw prints plugin logs + warnings around the JSON output even with --json.
    # Grab the first JSON object/array block heuristically.
    s = text.strip()
    if not s:
        raise _OpenClawError("OpenClaw 没有输出。")

    # Prefer last JSON-looking block.
    first_obj = s.find("{")
    first_arr = s.find("[")
    first = first_obj if first_arr == -1 else (first_arr if first_obj == -1 else min(first_obj, first_arr))
    if first == -1:
        raise _OpenClawError("无法从 OpenClaw 输出中解析 JSON。")

    # Find matching end by scanning from end for } or ].
    last_obj = s.rfind("}")
    last_arr = s.rfind("]")
    last = max(last_obj, last_arr)
    if last == -1 or last <= first:
        raise _OpenClawError("无法从 OpenClaw 输出中定位 JSON 结束位置。")

    blob = s[first : last + 1]
    return json.loads(blob)


class OpenClawBrowserProvider(JobProvider):
    """
    Real-time job link scanning using the local OpenClaw dedicated browser.

    This relies on a *human-attached* tab via the OpenClaw Chrome extension relay.
    Workflow:
      1) `openclaw browser start`
      2) Open any tab and click the OpenClaw extension icon to attach
      3) Then call `/api/jobs/search` with JOB_DATA_PROVIDER=openclaw

    This provider only returns job URLs for manual apply (no auto-submit).
    """

    name = "openclaw"

    def __init__(self, browser_profile: Optional[str] = None, timeout_s: int = 90):
        self.browser_profile = (browser_profile or os.getenv("OPENCLAW_BROWSER_PROFILE", "")).strip() or "chrome"
        self.timeout_s = timeout_s
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _oc(self, *args: str, json_out: bool = False, timeout_s: Optional[int] = None) -> _CmdResult:
        cmd = ["openclaw", "browser", "--browser-profile", self.browser_profile]
        if json_out:
            cmd.append("--json")
        cmd.extend(args)
        return _run(cmd, timeout_s=timeout_s or self.timeout_s)

    def _ensure_attached(self) -> None:
        r = self._oc("evaluate", "--fn", "(() => 1)", json_out=True, timeout_s=20)
        if r.code == 0:
            return
        msg = (r.stdout + "\n" + r.stderr).strip()
        if "no tab is connected" in msg.lower():
            raise _OpenClawError(
                "OpenClaw 浏览器已启动，但未连接任何标签页。\n"
                "请按这个顺序做：\n"
                "1) 运行 `openclaw browser start`\n"
                "2) 在弹出的 Chrome 里打开任意网页\n"
                "3) 点击工具栏里的 OpenClaw 扩展图标让它 Attach 到当前标签页\n"
                "然后再重试搜索。"
            )
        raise _OpenClawError(f"OpenClaw 浏览器不可用: {msg[:500]}")

    def _navigate_and_collect(self, url: str, want_hosts: List[str], limit: int) -> List[Tuple[str, str]]:
        self._ensure_attached()

        r = self._oc("navigate", url, timeout_s=60)
        if r.code != 0:
            raise _OpenClawError(f"导航失败: {(r.stdout + r.stderr)[:300]}")

        # Let SPA settle a bit.
        self._oc("wait", "--load", "domcontentloaded", "--timeout-ms", "20000", timeout_s=30)
        self._oc("wait", "--time", "1200", timeout_s=10)

        # Pull anchors.
        js = (
            "() => Array.from(document.querySelectorAll('a[href]')).map(a => ({"
            "href: a.href, text: (a.innerText || a.textContent || '').trim()"
            "})).filter(x => x.href && x.text && x.text.length >= 2).slice(0, 800)"
        )
        r2 = self._oc("evaluate", "--fn", js, json_out=True, timeout_s=30)
        if r2.code != 0:
            raise _OpenClawError(f"读取页面链接失败: {(r2.stdout + r2.stderr)[:300]}")

        data = _extract_json(r2.stdout + "\n" + r2.stderr)
        # Expected: {"value": ...} or direct array. Be defensive.
        items = data.get("value") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []

        out: List[Tuple[str, str]] = []
        seen: set[str] = set()
        for it in items:
            if len(out) >= limit:
                break
            if not isinstance(it, dict):
                continue
            href = str(it.get("href", "")).strip()
            title = str(it.get("text", "")).strip()
            if not href or not title:
                continue
            if href in seen:
                continue
            seen.add(href)
            if want_hosts and not any(h in href for h in want_hosts):
                continue
            out.append((title, href))
        return out[:limit]

    def _build_urls(self, params: JobSearchParams) -> List[Tuple[str, str, List[str]]]:
        keywords = " ".join([k for k in (params.keywords or []) if k]).strip() or "招聘"
        location = (params.location or "").strip()
        q = quote(f"{keywords} {location}".strip())

        return [
            ("Boss直聘", f"https://www.zhipin.com/web/geek/job?query={q}", ["zhipin.com"]),
            ("猎聘", f"https://www.liepin.com/zhaopin/?key={q}", ["liepin.com"]),
            ("智联招聘", f"https://sou.zhaopin.com/?kw={q}", ["zhaopin.com"]),
            ("前程无忧", f"https://search.51job.com/list/000000,000000,0000,00,9,99,{q},2,1.html", ["51job.com"]),
        ]

    def search_jobs(self, params: JobSearchParams) -> List[Dict[str, Any]]:
        # Always local-only.
        urls = self._build_urls(params)
        limit = max(1, min(int(params.limit or 50), 50))

        results: List[Dict[str, Any]] = []
        per_site = max(3, min(15, limit // max(1, len(urls))))

        for platform, url, hosts in urls:
            try:
                pairs = self._navigate_and_collect(url, hosts, per_site)
            except _OpenClawError:
                # Bubble up with actionable error rather than silent fallback.
                raise

            for title, link in pairs:
                job_id = f"openclaw_{abs(hash(link))}"
                job = {
                    "id": job_id,
                    "title": title,
                    "company": "",
                    "location": params.location or "",
                    "salary": "",
                    "description": "",
                    "requirements": [],
                    "platform": platform,
                    "link": link,
                    "updated": "",
                    "provider": self.name,
                }
                self._cache[job_id] = job
                results.append(job)
                if len(results) >= limit:
                    return results[:limit]

        return results[:limit]

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(job_id)

