from __future__ import annotations

import json
import os
import subprocess
import time
import shutil
import re
import hashlib
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
    # On Windows, `openclaw` is typically installed as a `.cmd` shim.
    # Resolve the actual executable to keep argument boundaries intact.
    exe = shutil.which(cmd[0]) or cmd[0]
    p = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=timeout_s, shell=False)
    return _CmdResult(p.returncode, p.stdout or "", p.stderr or "")


def _extract_json(text: str) -> Any:
    # OpenClaw prints plugin logs + warnings around the JSON output even with --json.
    # We strip ANSI codes and then use JSONDecoder.raw_decode to find the first
    # valid JSON value in the stream.
    s = (text or "").strip()
    if not s:
        raise _OpenClawError("OpenClaw 没有输出。")

    # Strip ANSI escape sequences.
    s = re.sub(r"\x1b\[[0-9;]*m", "", s)

    dec = json.JSONDecoder()
    for i, ch in enumerate(s):
        if ch not in "{[":
            continue
        try:
            obj, _ = dec.raw_decode(s[i:])
            return obj
        except json.JSONDecodeError:
            continue

    raise _OpenClawError("无法从 OpenClaw 输出中解析 JSON。")


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
        # OpenClaw returns {"result": ...}. Some commands may return {"value": ...}.
        items = (data.get("result") or data.get("value")) if isinstance(data, dict) else data
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
            # Platform-specific job link filters (reduce navigation/header noise).
            # Boss: only keep job detail links.
            if any("zhipin.com" in h for h in want_hosts):
                if "/job_detail/" not in href:
                    continue
            out.append((title, href))
        return out[:limit]

    def _build_urls(self, params: JobSearchParams) -> List[Tuple[str, str, List[str]]]:
        keywords = " ".join([k for k in (params.keywords or []) if k]).strip() or "招聘"
        location = (params.location or "").strip()
        q = quote(f"{keywords} {location}".strip())

        # Default to Boss only for MVP. You can expand via env:
        # OPENCLAW_JOB_SITES=boss,liepin,zhaopin,51job
        sites = (os.getenv("OPENCLAW_JOB_SITES", "") or "boss").strip().lower()
        enabled = {s.strip() for s in sites.split(",") if s.strip()}

        urls: List[Tuple[str, str, List[str]]] = []
        if "boss" in enabled or "zhipin" in enabled:
            urls.append(("Boss直聘", f"https://www.zhipin.com/web/geek/job?query={q}", ["zhipin.com"]))
        if "liepin" in enabled:
            urls.append(("猎聘", f"https://www.liepin.com/zhaopin/?key={q}", ["liepin.com"]))
        if "zhaopin" in enabled:
            urls.append(("智联招聘", f"https://sou.zhaopin.com/?kw={q}", ["zhaopin.com"]))
        if "51job" in enabled or "qcwy" in enabled:
            urls.append(("前程无忧", f"https://search.51job.com/list/000000,000000,0000,00,9,99,{q},2,1.html", ["51job.com"]))

        return urls or [("Boss直聘", f"https://www.zhipin.com/web/geek/job?query={q}", ["zhipin.com"])]

    def search_jobs(self, params: JobSearchParams, progress_callback=None) -> List[Dict[str, Any]]:
        # Always local-only.
        urls = self._build_urls(params)
        limit = max(1, min(int(params.limit or 50), 50))

        results: List[Dict[str, Any]] = []
        per_site = max(3, min(15, limit // max(1, len(urls))))

        total_sites = max(1, len(urls))
        for idx, (platform, url, hosts) in enumerate(urls):
            if progress_callback:
                try:
                    progress_callback(
                        f"打开 {platform} 搜索页并抓取链接...",
                        int((idx / total_sites) * 100),
                    )
                except Exception:
                    pass
            try:
                pairs = self._navigate_and_collect(url, hosts, per_site)
            except _OpenClawError:
                # Bubble up with actionable error rather than silent fallback.
                raise

            if progress_callback:
                try:
                    progress_callback(
                        f"{platform} 抓取到 {len(pairs)} 条链接，整理中...",
                        int(((idx + 0.7) / total_sites) * 100),
                    )
                except Exception:
                    pass

            for title, link in pairs:
                job_id = "openclaw_" + hashlib.sha1(link.encode("utf-8", errors="ignore")).hexdigest()[:16]
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
                    if progress_callback:
                        try:
                            progress_callback("完成", 100)
                        except Exception:
                            pass
                    return results[:limit]

        if progress_callback:
            try:
                progress_callback("完成", 100)
            except Exception:
                pass
        return results[:limit]

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(job_id)
