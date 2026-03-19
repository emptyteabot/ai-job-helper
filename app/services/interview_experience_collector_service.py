from __future__ import annotations

import html
import os
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import quote_plus, urlparse

import requests


def _strip_tags(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", text or "")
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _safe_domain(link: str) -> str:
    try:
        host = (urlparse(link).netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


class InterviewExperienceCollectorService:
    """
    Public interview-experience collector (MVP).

    Focus:
    - nowcoder / xiaohongshu source preference
    - unified response fields for API usage
    - keep legacy fields (`excerpt` / `link`) for frontend compatibility
    """

    SOURCE_DOMAINS: Dict[str, List[str]] = {
        "nowcoder": ["nowcoder.com"],
        "xiaohongshu": ["xiaohongshu.com", "xiaohongshu.cn", "xhslink.com", "xhs.cn"],
        "zhihu": ["zhihu.com"],
        "juejin": ["juejin.cn"],
        "csdn": ["csdn.net"],
    }
    SOURCE_ALIASES: Dict[str, str] = {
        "nowcoder": "nowcoder",
        "niuke": "nowcoder",
        "xiaohongshu": "xiaohongshu",
        "xhs": "xiaohongshu",
        "zhihu": "zhihu",
        "juejin": "juejin",
        "csdn": "csdn",
    }

    DEFAULT_SOURCES: List[str] = ["nowcoder", "xiaohongshu", "zhihu", "juejin", "csdn"]

    def __init__(self) -> None:
        self.timeout_s = int((os.getenv("INTERVIEW_SOURCE_TIMEOUT", "12") or "12").strip())
        self.max_per_engine = int((os.getenv("INTERVIEW_SOURCE_LIMIT", "10") or "10").strip())
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
            }
        )

    def search(
        self,
        keywords: Iterable[str],
        location: str = "",
        sources: Optional[Iterable[str]] = None,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        target = max(1, min(int(limit or 12), 30))
        source_list = self._normalize_sources(sources)
        query = self._build_query(list(keywords or []), location, source_list)

        rows: List[Dict[str, Any]] = []
        rows.extend(self._search_bing_rss(query, limit=self.max_per_engine))
        rows.extend(self._search_duckduckgo(query, limit=self.max_per_engine))

        if len(rows) < 4:
            broader = self._build_query([], location, source_list)
            if broader != query:
                rows.extend(self._search_bing_rss(broader, limit=self.max_per_engine))
                rows.extend(self._search_duckduckgo(broader, limit=self.max_per_engine))

        normalized = self._normalize_rows(rows, source_list)
        ranked = self._dedupe_and_rank(normalized, source_list)
        if ranked:
            return ranked[:target]
        return self._fallback_rows(source_list, target)

    def _normalize_sources(self, sources: Optional[Iterable[str]]) -> List[str]:
        out: List[str] = []
        for s in sources or []:
            raw = str(s or "").strip()
            key = self.SOURCE_ALIASES.get(raw.lower()) or self.SOURCE_ALIASES.get(raw) or raw.lower()
            if not key:
                continue
            if key in self.SOURCE_DOMAINS and key not in out:
                out.append(key)
        if out:
            return out
        return list(self.DEFAULT_SOURCES)

    def _build_query(self, keywords: List[str], location: str, sources: List[str]) -> str:
        picks: List[str] = []
        for item in keywords:
            t = str(item or "").strip()
            if not t:
                continue
            picks.append(t)
            if len(picks) >= 4:
                break

        site_tokens: List[str] = []
        for src in sources:
            for d in self.SOURCE_DOMAINS.get(src, []):
                site_tokens.append(f"site:{d}")
        site_expr = " OR ".join(site_tokens)

        parts: List[str] = []
        if location:
            parts.append(str(location).strip())
        if picks:
            parts.append(" ".join(picks))
        parts.append("面经 面试 复盘 真题")
        if site_expr:
            parts.append(site_expr)
        return " ".join(p for p in parts if p).strip()

    def _search_bing_rss(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not query:
            return []
        url = f"https://www.bing.com/search?q={quote_plus(query)}&format=rss"
        try:
            resp = self.session.get(url, timeout=self.timeout_s)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
        except Exception:
            return []

        rows: List[Dict[str, Any]] = []
        for item in root.findall(".//item"):
            title = _strip_tags(item.findtext("title", default=""))
            link = (item.findtext("link", default="") or "").strip()
            desc = _strip_tags(item.findtext("description", default=""))
            if not title or not link:
                continue
            rows.append(
                {
                    "title": title,
                    "snippet": desc,
                    "url": link,
                    "domain": _safe_domain(link),
                    "engine": "bing_rss",
                }
            )
            if len(rows) >= max(1, int(limit or 10)):
                break
        return rows

    def _search_duckduckgo(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not query:
            return []
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            resp = self.session.get(url, timeout=self.timeout_s)
            resp.raise_for_status()
            html_text = resp.text
        except Exception:
            return []

        rows: List[Dict[str, Any]] = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="(?P<link>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
            r'(?:<a[^>]+class="result__snippet"[^>]*>|<div[^>]+class="result__snippet"[^>]*>)'
            r'(?P<snippet>.*?)</(?:a|div)>',
            flags=re.S | re.I,
        )
        for m in pattern.finditer(html_text):
            link = html.unescape((m.group("link") or "").strip())
            title = _strip_tags(m.group("title") or "")
            snippet = _strip_tags(m.group("snippet") or "")
            if not title or not link:
                continue
            rows.append(
                {
                    "title": title,
                    "snippet": snippet,
                    "url": link,
                    "domain": _safe_domain(link),
                    "engine": "duckduckgo",
                }
            )
            if len(rows) >= max(1, int(limit or 10)):
                break
        return rows

    def _detect_source(self, domain: str, title: str, summary: str, url: str) -> str:
        d = (domain or "").lower()
        joined = f"{title} {summary} {url} {d}".lower()
        for src, domains in self.SOURCE_DOMAINS.items():
            for one in domains:
                if one in joined:
                    return src
        return "other"

    def _extract_published_at(self, text: str) -> str:
        t = text or ""
        # 2026-03-19 / 2026/03/19 / 2026.03.19 / 2026年03月19日
        m = re.search(
            r"(20\d{2})\s*(?:[-/.]|\u5e74)\s*(\d{1,2})\s*(?:[-/.]|\u6708)\s*(\d{1,2})(?:\s*\u65e5)?",
            t,
            flags=re.I,
        )
        if not m:
            return ""
        y, mm, dd = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
        return f"{y}-{mm}-{dd}"

    def _normalize_rows(self, rows: List[Dict[str, Any]], sources: List[str]) -> List[Dict[str, Any]]:
        source_set: Set[str] = set(sources)
        out: List[Dict[str, Any]] = []
        for row in rows or []:
            title = str(row.get("title") or "").strip()
            summary = str(row.get("snippet") or "").strip()
            url = str(row.get("url") or "").strip()
            domain = str(row.get("domain") or "").strip().lower()
            engine = str(row.get("engine") or "").strip()
            if not title or not url:
                continue

            source = self._detect_source(domain, title, summary, url)
            if source_set and source != "other" and source not in source_set:
                continue
            if source_set and source == "other":
                # For a source-constrained query, drop unrelated domains.
                continue

            published_at = self._extract_published_at(f"{title} {summary}")
            out.append(
                {
                    "title": title,
                    "summary": summary,
                    "source": source,
                    "domain": domain,
                    "url": url,
                    "published_at": published_at,
                    "engine": engine,
                    # legacy compatibility fields
                    "excerpt": summary,
                    "link": url,
                }
            )
        return out

    def _dedupe_and_rank(self, rows: List[Dict[str, Any]], sources: List[str]) -> List[Dict[str, Any]]:
        source_priority = {
            "nowcoder": 12,
            "xiaohongshu": 11,
            "zhihu": 9,
            "juejin": 8,
            "csdn": 7,
            "other": 1,
        }
        seen: Dict[str, Dict[str, Any]] = {}
        for row in rows or []:
            key = str(row.get("url") or "").strip().lower()
            if not key:
                continue
            cur = seen.get(key)
            if not cur:
                seen[key] = row
                continue
            if len(str(row.get("summary") or "")) > len(str(cur.get("summary") or "")):
                seen[key] = row

        def score(row: Dict[str, Any]) -> int:
            title = str(row.get("title") or "").lower()
            summary = str(row.get("summary") or "").lower()
            src = str(row.get("source") or "other").lower()
            s = source_priority.get(src, 1)
            for token in ("面经", "面试", "复盘", "真题", "高频", "经验"):
                if token in title:
                    s += 3
                if token in summary:
                    s += 1
            return s

        ranked = list(seen.values())
        ranked.sort(key=score, reverse=True)
        return ranked

    def _fallback_rows(self, sources: List[str], limit: int) -> List[Dict[str, Any]]:
        presets: List[Dict[str, Any]] = [
            {
                "title": "牛客面经：后端高频题复盘清单",
                "summary": "建议优先准备项目深挖、缓存一致性、索引与慢查询、服务稳定性复盘。",
                "source": "nowcoder",
                "domain": "nowcoder.com",
                "url": "",
                "published_at": "",
                "engine": "fallback",
            },
            {
                "title": "小红书面经：AI 应用岗面试问题整理",
                "summary": "重点准备模型选型、成本控制、线上评估、以及失败案例复盘。",
                "source": "xiaohongshu",
                "domain": "xiaohongshu.com",
                "url": "",
                "published_at": "",
                "engine": "fallback",
            },
        ]
        source_set = set(sources)
        rows: List[Dict[str, Any]] = []
        for p in presets:
            if source_set and p["source"] not in source_set:
                continue
            row = dict(p)
            row["excerpt"] = row["summary"]
            row["link"] = row["url"]
            rows.append(row)
        return rows[: max(1, int(limit or 1))]
