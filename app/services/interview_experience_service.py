from __future__ import annotations

import html
import os
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterable, List, Optional
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


class InterviewExperienceService:
    """
    Lightweight interview-experience aggregation from public search endpoints.
    No browser automation required; works in most cloud/server environments.
    """

    def __init__(self) -> None:
        self.timeout_s = int((os.getenv("INTERVIEW_SOURCE_TIMEOUT", "12") or "12").strip())
        self.max_per_source = int((os.getenv("INTERVIEW_SOURCE_LIMIT", "8") or "8").strip())
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
            }
        )

        self.domain_priority = {
            "nowcoder.com": 12,
            "xiaohongshu.com": 11,
            "xiaohongshu.cn": 11,
            "xhs.cn": 11,
            "xhslink.com": 11,
            "zhihu.com": 10,
            "juejin.cn": 8,
            "csdn.net": 8,
            "51cto.com": 7,
            "v2ex.com": 6,
            "toutiao.com": 5,
            "sohu.com": 4,
        }
        self.source_domains = {
            "nowcoder": ["nowcoder.com"],
            "xiaohongshu": ["xiaohongshu.com", "xiaohongshu.cn", "xhs.cn", "xhslink.com"],
            "zhihu": ["zhihu.com"],
            "juejin": ["juejin.cn"],
            "csdn": ["csdn.net"],
        }
        self.source_aliases = {
            "nowcoder": "nowcoder",
            "niuke": "nowcoder",
            "xiaohongshu": "xiaohongshu",
            "xhs": "xiaohongshu",
            "zhihu": "zhihu",
            "juejin": "juejin",
            "csdn": "csdn",
        }

    def search_experiences(
        self,
        keywords: Iterable[str],
        location: str = "",
        limit: int = 12,
        sources: Optional[Iterable[str]] = None,
        unified: bool = False,
    ) -> List[Dict[str, Any]]:
        target = max(1, min(int(limit or 12), 30))
        query = self._build_query(list(keywords or []), location)

        rows: List[Dict[str, Any]] = []
        rows.extend(self._search_bing_rss(query, limit=self.max_per_source))
        rows.extend(self._search_duckduckgo(query, limit=self.max_per_source))

        # Retry with broader query if narrow query has few usable results.
        if len(rows) < 4:
            broader_query = self._build_query([], location)
            if broader_query != query:
                rows.extend(self._search_bing_rss(broader_query, limit=self.max_per_source))
                rows.extend(self._search_duckduckgo(broader_query, limit=self.max_per_source))

        deduped = self._dedupe_and_rank(rows)
        if deduped:
            selected = deduped[:target]
        else:
            selected = self._fallback_rows(target)
        if unified or sources:
            return self.normalize_rows(selected, sources=sources, limit=target)
        return selected

    def render_digest(self, rows: List[Dict[str, Any]], top_n: int = 6) -> str:
        selected = (rows or [])[: max(1, int(top_n or 6))]
        if not selected:
            return "暂无可用面试经历，建议先查看目标岗位 JD 并整理 STAR 项目复盘。"

        lines = ["【全网面试经历要点】"]
        for idx, row in enumerate(selected, 1):
            title = str(row.get("title") or "面试经验").strip()
            domain = str(row.get("domain") or "").strip()
            excerpt = str(row.get("excerpt") or "").strip()
            if len(excerpt) > 120:
                excerpt = excerpt[:117] + "..."
            line = f"{idx}. {title}"
            if domain:
                line += f"（{domain}）"
            lines.append(line)
            if excerpt:
                lines.append(f"   - {excerpt}")
        return "\n".join(lines)

    def _build_query(self, keywords: List[str], location: str = "") -> str:
        picks: List[str] = []
        for item in keywords:
            text = str(item or "").strip()
            if not text:
                continue
            if text.lower() in {"python", "java", "go", "golang", "backend", "frontend", "ai"}:
                picks.append(text + " 面经")
            else:
                picks.append(text)
            if len(picks) >= 4:
                break

        parts = [
            "面试 经验 复盘",
            (
                "site:nowcoder.com OR site:xiaohongshu.com OR site:xiaohongshu.cn "
                "OR site:zhihu.com OR site:juejin.cn OR site:csdn.net"
            ),
        ]
        if picks:
            parts.insert(0, " ".join(picks))
        if location:
            parts.insert(0, str(location).strip())
        return " ".join(parts).strip()

    def _search_bing_rss(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
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
            domain = _safe_domain(link)
            rows.append(
                {
                    "title": title,
                    "link": link,
                    "excerpt": desc,
                    "domain": domain,
                    "source": "bing_rss",
                }
            )
            if len(rows) >= max(1, limit):
                break
        return rows

    def _search_duckduckgo(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
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
            r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
            flags=re.S | re.I,
        )
        for m in pattern.finditer(html_text):
            link = html.unescape((m.group("link") or "").strip())
            title = _strip_tags(m.group("title") or "")
            snippet = _strip_tags(m.group("snippet") or "")
            if not title or not link:
                continue
            domain = _safe_domain(link)
            rows.append(
                {
                    "title": title,
                    "link": link,
                    "excerpt": snippet,
                    "domain": domain,
                    "source": "duckduckgo",
                }
            )
            if len(rows) >= max(1, limit):
                break
        return rows

    def _dedupe_and_rank(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Dict[str, Dict[str, Any]] = {}
        for row in rows or []:
            title = str(row.get("title") or "").strip()
            link = str(row.get("link") or "").strip()
            if not title or not link:
                continue
            key = (link.lower() or title.lower())
            cur = seen.get(key)
            if not cur:
                seen[key] = row
                continue
            # Keep the richer excerpt.
            if len(str(row.get("excerpt") or "")) > len(str(cur.get("excerpt") or "")):
                seen[key] = row

        ranked = list(seen.values())

        def score(row: Dict[str, Any]) -> int:
            title = str(row.get("title") or "").lower()
            excerpt = str(row.get("excerpt") or "").lower()
            domain = str(row.get("domain") or "").lower()
            s = 0
            s += self.domain_priority.get(domain, 1)
            for token in ("面经", "面试", "复盘", "高频", "真题", "经验"):
                if token in title:
                    s += 3
                if token in excerpt:
                    s += 1
            if "广告" in title or "推广" in title:
                s -= 6
            return s

        ranked.sort(key=score, reverse=True)
        return ranked

    def _normalize_sources(self, sources: Optional[Iterable[str]]) -> List[str]:
        out: List[str] = []
        for s in sources or []:
            raw = str(s or "").strip()
            if not raw:
                continue
            key = self.source_aliases.get(raw.lower()) or self.source_aliases.get(raw) or raw.lower()
            if key in self.source_domains and key not in out:
                out.append(key)
        return out

    def _detect_source(self, domain: str, title: str, excerpt: str, link: str) -> str:
        joined = f"{domain} {title} {excerpt} {link}".lower()
        for source, domains in self.source_domains.items():
            for one in domains:
                if one in joined:
                    return source
        return "other"

    def _extract_published_at(self, text: str) -> str:
        t = text or ""
        m = re.search(
            r"(20\d{2})\s*(?:[-/.]|\u5e74)\s*(\d{1,2})\s*(?:[-/.]|\u6708)\s*(\d{1,2})(?:\s*\u65e5)?",
            t,
            flags=re.I,
        )
        if not m:
            return ""
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"

    def normalize_rows(
        self,
        rows: List[Dict[str, Any]],
        sources: Optional[Iterable[str]] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        source_filter = set(self._normalize_sources(sources))
        target = max(1, min(int(limit or 30), 30))
        out: List[Dict[str, Any]] = []
        for row in rows or []:
            title = str(row.get("title") or "").strip()
            summary = str(row.get("summary") or row.get("excerpt") or "").strip()
            url = str(row.get("url") or row.get("link") or "").strip()
            domain = str(row.get("domain") or "").strip().lower()
            if not domain and url:
                domain = _safe_domain(url)
            if not title:
                continue

            source_raw = str(row.get("source") or "").strip().lower()
            source = self.source_aliases.get(source_raw, source_raw)
            if source in {"", "bing_rss", "duckduckgo", "fallback"}:
                source = self._detect_source(domain, title, summary, url)

            if source_filter and source not in source_filter:
                continue

            published_at = str(row.get("published_at") or "").strip() or self._extract_published_at(
                f"{title} {summary}"
            )
            out.append(
                {
                    "title": title,
                    "summary": summary,
                    "source": source,
                    "domain": domain,
                    "url": url,
                    "published_at": published_at,
                    "engine": str(row.get("source") or "legacy"),
                    "excerpt": summary,
                    "link": url,
                }
            )
            if len(out) >= target:
                break
        return out

    def _fallback_rows(self, limit: int) -> List[Dict[str, Any]]:
        rows = [
            {
                "title": "牛客面经：后端岗位常见一面高频题整理",
                "link": "",
                "excerpt": "重点准备：项目深挖、数据库索引、缓存一致性、并发与故障回放。",
                "domain": "nowcoder.com",
                "source": "nowcoder",
            },
            {
                "title": "小红书面经：AI/算法岗位面试复盘通用框架",
                "link": "",
                "excerpt": "重点准备：数据集、评估指标、线上回归、成本-效果取舍和失败案例复盘。",
                "domain": "xiaohongshu.com",
                "source": "xiaohongshu",
            },
            {
                "title": "行为面试 STAR 拆解模板",
                "link": "",
                "excerpt": "每个故事必须包含目标、约束、动作、量化结果和复盘。",
                "domain": "local_fallback",
                "source": "fallback",
            },
        ]
        return rows[: max(1, limit)]
