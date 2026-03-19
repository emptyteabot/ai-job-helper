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
                "❌ OpenClaw 浏览器未连接标签页\n\n"
                "📋 解决步骤（只需做一次）：\n"
                "1️⃣ 打开命令行，运行: openclaw browser start\n"
                "2️⃣ 在弹出的Chrome中访问Boss直聘: https://www.zhipin.com\n"
                "3️⃣ 点击浏览器右上角的OpenClaw扩展图标（🔧）\n"
                "4️⃣ 点击 'Attach' 按钮连接当前标签页\n"
                "5️⃣ 返回本页面，重新点击搜索\n\n"
                "💡 提示：连接一次后，只要不关闭浏览器就一直有效"
            )
        if "command not found" in msg.lower() or "not recognized" in msg.lower():
            raise _OpenClawError(
                "❌ OpenClaw 未安装\n\n"
                "📦 安装步骤：\n"
                "1️⃣ 安装Python包: pip install openclaw\n"
                "2️⃣ 安装Chrome扩展: openclaw browser install-extension\n"
                "3️⃣ 重启浏览器\n"
                "4️⃣ 返回本页面重试\n\n"
                "📖 详细文档: docs/howto/OPENCLAW_BOSS_MVP.md"
            )
        raise _OpenClawError(f"❌ OpenClaw 错误: {msg[:500]}\n\n请检查OpenClaw是否正确安装和配置")

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

    def _search_terms(self, params: JobSearchParams) -> List[str]:
        terms: List[str] = []
        for token in (params.keywords or []):
            for seg in str(token or "").lower().split():
                seg = seg.strip()
                if len(seg) >= 2:
                    terms.append(seg)
        return terms

    def _score_job(self, job: Dict[str, Any], terms: List[str], target_location: str) -> float:
        title = str(job.get("title") or "").lower()
        link = str(job.get("link") or "").lower()
        location = str(job.get("location") or "").lower()

        score = 0.0
        for term in terms:
            if term in title:
                score += 3.0
            if term in link:
                score += 1.0
        if target_location and target_location in location:
            score += 2.0
        if "/job_detail/" in link:
            score += 1.0
        return score

    def _dedupe_and_rank(
        self,
        jobs: List[Dict[str, Any]],
        params: JobSearchParams,
        limit: int,
    ) -> List[Dict[str, Any]]:
        terms = self._search_terms(params)
        target_location = str(params.location or "").strip().lower()

        deduped: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for job in jobs:
            link = str(job.get("link") or "").strip().lower()
            jid = str(job.get("id") or "").strip().lower()
            title = str(job.get("title") or "").strip().lower()
            key = link or jid or title
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(job)

        deduped.sort(key=lambda one: self._score_job(one, terms, target_location), reverse=True)
        return deduped[:limit]

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

        ranked = self._dedupe_and_rank(results, params=params, limit=limit)
        if progress_callback:
            try:
                progress_callback("完成", 100)
            except Exception:
                pass
        return ranked

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(job_id)

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查：检测OpenClaw是否可用
        
        Returns:
            {
                "available": bool,
                "status": str,
                "message": str,
                "browser_connected": bool,
                "tab_attached": bool
            }
        """
        result = {
            "available": False,
            "status": "error",
            "message": "",
            "browser_connected": False,
            "tab_attached": False
        }
        
        # 1. 检查OpenClaw命令是否存在
        if not shutil.which("openclaw"):
            result["message"] = "OpenClaw未安装。请运行: pip install openclaw"
            return result
        
        result["browser_connected"] = True
        
        # 2. 检查是否有标签页连接
        try:
            r = self._oc("evaluate", "--fn", "(() => 1)", json_out=True, timeout_s=10)
            if r.code == 0:
                result["available"] = True
                result["status"] = "ok"
                result["tab_attached"] = True
                result["message"] = "✅ OpenClaw已就绪，可以抓取Boss直聘岗位"
                return result
            
            msg = (r.stdout + "\n" + r.stderr).strip().lower()
            if "no tab is connected" in msg:
                result["message"] = (
                    "⚠️ OpenClaw已安装，但未连接标签页。\n"
                    "请在Chrome中打开Boss直聘，点击OpenClaw扩展图标并Attach"
                )
            else:
                result["message"] = f"⚠️ OpenClaw异常: {msg[:200]}"
                
        except Exception as e:
            result["message"] = f"⚠️ OpenClaw检查失败: {str(e)}"
        
        return result
