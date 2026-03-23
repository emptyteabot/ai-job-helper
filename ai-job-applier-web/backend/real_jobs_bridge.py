"""Helper that bridges the web backend to the desktop real job service."""

from __future__ import annotations

import html
import hashlib
import importlib
import importlib.util
import json
import logging
import os
import random
import re
import sys
import types
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

try:
    _DESKTOP_BACKEND_PATH = Path(__file__).resolve().parents[2] / "ai-job-applier-desktop" / "backend"
except IndexError:
    _DESKTOP_BACKEND_PATH = None

_REAL_JOB_MODULE = "data.real_job_service"
_SERVICE_INSTANCE: Optional[Any] = None
_SERVICE_READY: bool = False
_SERVICE_LOGGED_FAILURE: bool = False
_OPENCLAW_PROVIDER: Optional[Any] = None

_FALLBACK_TEMPLATES = [
    {
        "title": "Senior Python Backend Engineer",
        "platform": "BossZhipin",
        "salary_range": ["32-45K", "38-52K", "45-60K"],
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        "description": "Own API services, observability, and stability for large-scale platforms.",
    },
    {
        "title": "Full-Stack Engineer (React/Vue)",
        "platform": "Liepin",
        "salary_range": ["26-38K", "30-45K", "35-50K"],
        "skills": ["TypeScript", "React", "Vue", "Node.js", "GraphQL"],
        "description": "Ship new product surfaces and iterate with design and data partners.",
    },
    {
        "title": "AI/ML Platform Engineer",
        "platform": "OpenClaw",
        "salary_range": ["35-55K", "42-65K"],
        "skills": ["Python", "PyTorch", "Kubeflow", "TensorFlow", "AWS"],
        "description": "Deliver training pipelines, model monitoring, and inference infrastructure.",
    },
    {
        "title": "Product Manager, Automation",
        "platform": "BraveSearch",
        "salary_range": ["30-50K", "38-58K"],
        "skills": ["Product Strategy", "Automation", "OKR", "User Research"],
        "description": "Define automation roadmaps and lead cross-functional launches.",
    },
    {
        "title": "DevOps Engineer",
        "platform": "BaiduSearch",
        "salary_range": ["28-42K", "32-48K"],
        "skills": ["Linux", "Docker", "Kubernetes", "Monitoring", "Terraform"],
        "description": "Build resilient CI/CD and observability across hybrid clouds.",
    },
    {
        "title": "Data Analyst",
        "platform": "Jooble",
        "salary_range": ["22-32K", "26-38K"],
        "skills": ["SQL", "Python", "Pandas", "Looker", "Storytelling"],
        "description": "Turn messy signals into actionable insights and dashboards.",
    },
]

_FALLBACK_COMPANIES = [
    "NovaCore Labs",
    "BrightEdge Studio",
    "Cascade Finance",
    "Pioneer Robotics",
    "SignalUp Media",
    "Vertex Logistics",
    "Atlas Intelligence",
    "Blue Harbor Capital",
    "Prism Commerce",
    "QuantumNest",
]

_FALLBACK_LOCATIONS = ["Shanghai", "Beijing", "Shenzhen", "Hangzhou", "Guangzhou", "Chengdu", "Nanjing"]

_FALLBACK_BENEFITS = [
    "Stock options",
    "Flexible remote policy",
    "Quarterly bonus",
    "Wellness stipend",
    "Learning allowance",
    "Annual travel budget",
    "Family support",
    "Health coverage",
]

_SEARCH_ENGINE_HOSTS = (
    "duckduckgo.com",
    "bing.com",
    "google.com",
    "baidu.com",
    "sogou.com",
    "so.com",
    "yahoo.com",
)

_PORTAL_PATH_MARKERS = (
    "/web/geek/job",
    "/jobs/search",
    "/jobs/list",
    "/search",
    "/results",
)

_DETAIL_PATH_MARKERS = (
    "job_detail",
    "jobdetail",
    "job-details",
    "/job/",
    "/jobs/view",
    "/viewjob",
    "/position/",
    "/positions/",
)

_DETAIL_QUERY_KEYS = (
    "jobid",
    "job_id",
    "positionid",
    "position_id",
    "jid",
)


@dataclass
class SearchResult:
    jobs: List[Dict[str, Any]]
    provider: str
    warning: str = ""


def _normalize_keywords(keywords: Optional[Sequence[str]]) -> List[str]:
    return [str(item).strip() for item in (keywords or []) if str(item).strip()]


def _compose_warning(*parts: str) -> str:
    return "; ".join(part.strip() for part in parts if part and part.strip())


def _is_live_job(job: Dict[str, Any]) -> bool:
    provider = str(job.get("provider") or "").strip()
    link = _normalize_job_link(str(job.get("link") or job.get("url") or ""))
    if not link:
        return False
    if provider.startswith("fallback"):
        return False
    if _is_portal_or_search_link(link):
        return False
    return True


def _has_live_jobs(jobs: Sequence[Dict[str, Any]]) -> bool:
    return any(_is_live_job(job) for job in jobs)


def _derive_reported_provider(jobs: Sequence[Dict[str, Any]], provider: str) -> str:
    candidate = str(provider or "").strip()
    if candidate and candidate not in {"all", "local"} and not candidate.startswith("fallback"):
        return candidate

    for job in jobs:
        if not _is_live_job(job):
            continue
        source = str(job.get("source") or "").strip()
        job_provider = str(job.get("provider") or "").strip()
        if source == "legacy_backend":
            return "legacy_backend"
        if job_provider and job_provider not in {"all", "local"}:
            return job_provider
        if source:
            return source

    if _has_live_jobs(jobs):
        return "legacy_backend" if candidate in {"", "all", "local"} else candidate
    return candidate or "fallback"


def _sanitize_provider_warning(provider: str, warning: str) -> str:
    text = str(warning or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered in {"ok", "success"}:
        return ""
    if provider != "fallback" and text.startswith("Jobs sourced from"):
        return ""
    return text


def _prune_success_warnings(warnings: Sequence[str], provider: str) -> List[str]:
    if provider in {"fallback", "openclaw_challenge"}:
        return [item for item in warnings if item and item.strip()]

    suppressed_prefixes = (
        "OpenClaw provider unavailable",
        "OpenClaw unavailable",
        "OpenClaw search failed",
        "Desktop real job service unavailable",
        "Desktop real job service error",
        "Real web discovery did not yield",
        "No web discovery hits",
        "Fallback templates generated",
    )
    cleaned: List[str] = []
    for item in warnings:
        text = str(item or "").strip()
        if not text:
            continue
        if any(text.startswith(prefix) for prefix in suppressed_prefixes):
            continue
        cleaned.append(text)
    return cleaned


def _finalize_search_result(
    jobs: List[Dict[str, Any]],
    data_provider: str,
    warnings: Sequence[str],
    challenge_detected: bool,
) -> SearchResult:
    contexts = list(warnings)
    provider_key = str(data_provider or "").strip().lower()
    all_fallback_rows = bool(jobs) and all(
        str(row.get("provider") or "").strip().startswith("fallback") for row in jobs
    )
    if provider_key.startswith("fallback") or all_fallback_rows:
        stabilized_jobs = _dedupe_jobs(list(jobs))
        stabilization_warning = ""
    else:
        stabilized_jobs, stabilization_warning = _stabilize_jobs_for_execution(jobs)
    if stabilization_warning:
        contexts.append(stabilization_warning)
    reported_provider = (
        "openclaw_challenge" if challenge_detected else _derive_reported_provider(stabilized_jobs, data_provider)
    )
    contexts = _prune_success_warnings(contexts, reported_provider)
    return SearchResult(jobs=stabilized_jobs, provider=reported_provider, warning=_compose_warning(*contexts))


def _fallback_seed(keywords: Sequence[str], location: Optional[str], limit: int) -> int:
    parts = ["|".join(keywords), location or "", str(limit)]
    digest = hashlib.md5("||".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _http_get_text(url: str, timeout: int = 12) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def _http_get_json(url: str, timeout: int = 15) -> Dict[str, Any]:
    text = _http_get_text(url, timeout=timeout)
    return json.loads(text or "{}")


def _normalize_ddg_redirect(link: str) -> str:
    href = html.unescape((link or "").strip())
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/l/?"):
        href = "https://duckduckgo.com" + href
    if "duckduckgo.com/l/?" in href:
        query = parse_qs(urlparse(href).query)
        uddg = query.get("uddg", [])
        if uddg:
            return uddg[0]
    return href


def _normalize_job_link(link: str) -> str:
    href = _normalize_ddg_redirect(link)
    if not href:
        return ""
    parsed = urlparse(href)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return parsed._replace(fragment="").geturl()
    return href


def _host_matches(host: str, domain: str) -> bool:
    base = host[4:] if host.startswith("www.") else host
    return base == domain or base.endswith("." + domain)


def _classify_job_link(link: str) -> Tuple[str, int, bool, bool]:
    href = _normalize_job_link(link)
    if not href:
        return "missing_link", -200, False, True

    parsed = urlparse(href)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()
    query_map = parse_qs(parsed.query or "")
    is_direct_detail = any(marker in path for marker in _DETAIL_PATH_MARKERS) or any(
        key in query_map for key in _DETAIL_QUERY_KEYS
    )

    is_search_engine = any(_host_matches(host, domain) for domain in _SEARCH_ENGINE_HOSTS)
    has_portal_path = any(marker in path for marker in _PORTAL_PATH_MARKERS)
    has_search_query = any(key in query_map for key in ("q", "query", "keyword", "keywords", "wd", "search", "k"))
    is_portal_or_search = is_search_engine or ((has_portal_path or has_search_query) and not is_direct_detail)

    score = 0
    if parsed.scheme in {"http", "https"}:
        score += 5
    else:
        score -= 35
    if "zhipin.com" in host:
        score += 20
    if is_direct_detail:
        score += 120
    if any(token in path for token in ("job", "position", "career")):
        score += 10
    if is_portal_or_search:
        score -= 140
    if not parsed.netloc:
        score -= 15

    if is_direct_detail:
        quality = "direct_detail"
    elif is_portal_or_search:
        quality = "portal_or_search"
    elif score >= 20:
        quality = "detail_candidate"
    else:
        quality = "unknown_candidate"
    return quality, score, is_direct_detail, is_portal_or_search


def _is_portal_or_search_link(link: str) -> bool:
    _, _, _, is_portal_or_search = _classify_job_link(link)
    return is_portal_or_search


def _stabilize_jobs_for_execution(rows: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
    if not rows:
        return [], ""

    scored_rows: List[Tuple[int, int, bool, bool, Dict[str, Any]]] = []
    for index, row in enumerate(rows):
        item = dict(row)
        normalized_link = _normalize_job_link(str(item.get("link") or item.get("url") or ""))
        if normalized_link:
            item["link"] = normalized_link
        quality, score, is_direct_detail, is_portal_or_search = _classify_job_link(normalized_link)
        item["link_quality"] = quality
        item["link_quality_score"] = score
        item["is_direct_apply"] = bool(is_direct_detail)
        if is_direct_detail:
            item["apply_priority"] = "high"
        elif is_portal_or_search:
            item["apply_priority"] = "low"
        else:
            item["apply_priority"] = "medium"
        scored_rows.append((score, index, is_direct_detail, is_portal_or_search, item))

    ranked_rows = sorted(scored_rows, key=lambda entry: (-entry[0], entry[1]))
    direct_or_candidate = [entry for entry in ranked_rows if not entry[3]]
    portal_rows = [entry for entry in ranked_rows if entry[3]]
    has_direct_detail = any(entry[2] for entry in ranked_rows)

    if has_direct_detail:
        selected = direct_or_candidate
    elif direct_or_candidate:
        selected = direct_or_candidate
    else:
        selected = portal_rows[:1]

    dropped_portals = max(0, len(portal_rows) - sum(1 for entry in selected if entry[3]))
    stabilized_jobs = _dedupe_jobs([entry[4] for entry in selected])

    notes: List[str] = []
    if has_direct_detail:
        notes.append("Prioritized direct-apply detail pages.")
    if dropped_portals > 0:
        notes.append(f"Filtered {dropped_portals} portal/search entry links.")
    return stabilized_jobs, _compose_warning(*notes)


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip())


def _company_from_title(title: str) -> str:
    parts = [part.strip() for part in re.split(r"[-|_·]", title or "") if part.strip()]
    return parts[1] if len(parts) >= 2 else ""


def _dedupe_jobs(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        normalized_link = _normalize_job_link(str(row.get("link") or row.get("url") or "")).strip()
        key = normalized_link.lower()
        if not key or key in seen:
            continue
        if normalized_link:
            row["link"] = normalized_link
        seen.add(key)
        out.append(row)
    return out


def _search_duckduckgo_jobs(keyword: str, city: str, limit: int) -> List[Dict[str, Any]]:
    query = quote_plus(f"{city} {keyword} site:zhipin.com/job_detail")
    html_text = _http_get_text(f"https://duckduckgo.com/html/?q={query}")
    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="(?P<link>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.I | re.S,
    )
    rows: List[Dict[str, Any]] = []
    for index, match in enumerate(pattern.finditer(html_text), 1):
        link = _normalize_job_link(match.group("link"))
        quality, _, is_direct_detail, is_portal_or_search = _classify_job_link(link)
        if not link or is_portal_or_search or not is_direct_detail:
            continue
        title = _strip_html(match.group("title"))
        rows.append(
            {
                "id": f"ddg_{index}_{abs(hash(link))}",
                "title": title or f"{keyword} role",
                "company": _company_from_title(title),
                "salary": "",
                "location": city,
                "experience": "",
                "education": "",
                "description": "",
                "platform": "BossZhipin",
                "link": link,
                "provider": "duckduckgo",
                "source": "bridge",
                "link_quality": quality,
                "is_direct_apply": True,
                "apply_priority": "high",
            }
        )
        if len(rows) >= limit:
            break
    return _dedupe_jobs(rows)[:limit]


def _extract_openclaw_json(text: str) -> Any:
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        decoder = json.JSONDecoder()
        for index, char in enumerate(raw):
            if char not in "{[":
                continue
            try:
                obj, _ = decoder.raw_decode(raw[index:])
                return obj
            except Exception:
                continue
    return {}


def _openclaw_challenge_state(provider: Any) -> str:
    try:
        result = provider._oc("snapshot", json_out=True, timeout_s=20)
    except Exception:
        return ""
    payload = _extract_openclaw_json((result.stdout or "") + "\n" + (result.stderr or ""))
    text = json.dumps(payload, ensure_ascii=False)
    lowered = text.lower()
    markers = (
        "安全验证",
        "验证码",
        "点击按钮进行验证",
        "passport/zp/verify",
        "security.html",
    )
    for marker in markers:
        if marker.lower() in lowered:
            return "challenge_required"
    return ""


def _is_challenge_message(message: str) -> bool:
    text = str(message or "").lower()
    markers = (
        "verify",
        "security",
        "captcha",
        "安全验证",
        "验证码",
        "passport/zp/verify",
        "security.html",
    )
    return any(marker.lower() in text for marker in markers)


def _search_bing_jobs(keyword: str, city: str, limit: int) -> List[Dict[str, Any]]:
    query = quote_plus(f"{city} {keyword} site:zhipin.com/job_detail")
    html_text = _http_get_text(f"https://www.bing.com/search?q={query}")
    pattern = re.compile(
        r'<li class="b_algo"[^>]*>.*?<h2><a href="(?P<link>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.I | re.S,
    )
    rows: List[Dict[str, Any]] = []
    for index, match in enumerate(pattern.finditer(html_text), 1):
        link = _normalize_job_link(match.group("link"))
        quality, _, is_direct_detail, is_portal_or_search = _classify_job_link(link)
        if not link or is_portal_or_search or not is_direct_detail:
            continue
        title = _strip_html(match.group("title"))
        rows.append(
            {
                "id": f"bing_{index}_{abs(hash(link))}",
                "title": title or f"{keyword} role",
                "company": _company_from_title(title),
                "salary": "",
                "location": city,
                "experience": "",
                "education": "",
                "description": "",
                "platform": "BossZhipin",
                "link": link,
                "provider": "bing",
                "source": "bridge",
                "link_quality": quality,
                "is_direct_apply": True,
                "apply_priority": "high",
            }
        )
        if len(rows) >= limit:
            break
    return _dedupe_jobs(rows)[:limit]


def _real_web_discovery(keyword: str, city: str, limit: int) -> Tuple[List[Dict[str, Any]], str, str]:
    fetchers = [
        ("duckduckgo", _search_duckduckgo_jobs),
        ("bing", _search_bing_jobs),
    ]
    scopes: List[Tuple[str, str]] = []
    if city:
        scopes.append((f"city '{city}'", city))
    scopes.append(("global", ""))
    aggregated_warnings: List[str] = []

    for scope_label, scope_value in scopes:
        collector: List[Tuple[int, int, str, List[Dict[str, Any]]]] = []
        stage_warnings: List[str] = []
        for index, (provider_name, fetcher) in enumerate(fetchers):
            try:
                jobs = fetcher(keyword, scope_value, limit)
                if jobs:
                    collector.append((len(jobs), -index, provider_name, jobs))
            except Exception as exc:
                msg = f"{provider_name} discovery failed during {scope_label} search: {exc}"
                stage_warnings.append(msg)
                logger.warning(
                    "Real web discovery provider %s failed during %s scope search: %s",
                    provider_name,
                    scope_label,
                    exc,
                    exc_info=True,
                )
        aggregated_warnings.extend(stage_warnings)
        if collector:
            _, _, provider_name, jobs = max(collector, key=lambda entry: (entry[0], entry[1]))
            aggregated_warnings.append(f"Real web discovery satisfied {scope_label} with {provider_name}.")
            return jobs, provider_name, _compose_warning(*aggregated_warnings)
        aggregated_warnings.append(f"No web discovery hits for {scope_label}.")

    return [], "web_discovery", _compose_warning(*aggregated_warnings)


def _load_real_job_service() -> Optional[Any]:
    global _SERVICE_INSTANCE, _SERVICE_READY, _SERVICE_LOGGED_FAILURE
    if _SERVICE_READY and _SERVICE_INSTANCE:
        return _SERVICE_INSTANCE

    if not _DESKTOP_BACKEND_PATH or not _DESKTOP_BACKEND_PATH.exists():
        if not _SERVICE_LOGGED_FAILURE:
            logger.warning("Desktop backend path %s is unavailable", _DESKTOP_BACKEND_PATH)
            _SERVICE_LOGGED_FAILURE = True
        return None

    try:
        _ensure_desktop_aliases()
        path_str = str(_DESKTOP_BACKEND_PATH)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
        module = importlib.import_module(_REAL_JOB_MODULE)
        service_cls = getattr(module, "RealJobService")
        _SERVICE_INSTANCE = service_cls()
        _SERVICE_READY = True
        _SERVICE_LOGGED_FAILURE = False
        return _SERVICE_INSTANCE
    except Exception as exc:  # pragma: no cover - degrade gracefully
        if not _SERVICE_LOGGED_FAILURE:
            logger.warning("Unable to initialize RealJobService from %s: %s", _DESKTOP_BACKEND_PATH, exc, exc_info=True)
            _SERVICE_LOGGED_FAILURE = True
        _SERVICE_READY = False
        return None


def _load_openclaw_provider() -> Optional[Any]:
    global _OPENCLAW_PROVIDER
    if _OPENCLAW_PROVIDER is not None:
        return _OPENCLAW_PROVIDER
    try:
        _ensure_desktop_aliases()
        path_str = str(_DESKTOP_BACKEND_PATH)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
        module = importlib.import_module("app.services.job_providers.openclaw_browser_provider")
        provider_cls = getattr(module, "OpenClawBrowserProvider")
        _OPENCLAW_PROVIDER = provider_cls(browser_profile="openclaw")
        return _OPENCLAW_PROVIDER
    except Exception:
        return None


def _ensure_desktop_aliases() -> None:
    app_module = sys.modules.setdefault("app", types.ModuleType("app"))
    services_module = sys.modules.setdefault("app.services", types.ModuleType("app.services"))
    job_pkg = sys.modules.setdefault("app.services.job_providers", types.ModuleType("app.services.job_providers"))

    setattr(app_module, "services", services_module)
    setattr(services_module, "job_providers", job_pkg)

    mapping = {
        "app.services.application_record_service": _DESKTOP_BACKEND_PATH / "data" / "application_record_service.py",
        "app.services.job_providers.base": _DESKTOP_BACKEND_PATH / "data" / "job_providers" / "base.py",
        "app.services.job_providers.jooble_provider": _DESKTOP_BACKEND_PATH / "data" / "job_providers" / "jooble_provider.py",
        "app.services.job_providers.bing_provider": _DESKTOP_BACKEND_PATH / "data" / "job_providers" / "bing_provider.py",
        "app.services.job_providers.baidu_provider": _DESKTOP_BACKEND_PATH / "data" / "job_providers" / "baidu_provider.py",
        "app.services.job_providers.brave_provider": _DESKTOP_BACKEND_PATH / "data" / "job_providers" / "brave_provider.py",
        "app.services.job_providers.openclaw_browser_provider": _DESKTOP_BACKEND_PATH / "data" / "job_providers" / "openclaw_browser_provider.py",
    }

    for module_name, file_path in mapping.items():
        if module_name in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)


def service_is_available() -> bool:
    """Return True when the desktop real job service can be imported."""

    return _load_real_job_service() is not None


class RealJobsBridge:
    LEGACY_HEALTH_TTL = timedelta(seconds=30)

    def __init__(self) -> None:
        self.desktop_backend_url = (os.getenv("DESKTOP_BACKEND_URL", "") or "").strip().rstrip("/")
        self._last_live_provider: Optional[str] = None
        self._legacy_health_cache: Optional[SearchResult] = None
        self._legacy_health_checked_at: Optional[datetime] = None

    def _capture_search_result(self, result: SearchResult) -> SearchResult:
        if result.provider and _has_live_jobs(result.jobs) and not result.provider.startswith("fallback"):
            self._last_live_provider = result.provider
        else:
            self._last_live_provider = None
        return result

    def _finalize_and_record(
        self,
        jobs: List[Dict[str, Any]],
        data_provider: str,
        warnings: Sequence[str],
        challenge_detected: bool,
    ) -> SearchResult:
        result = _finalize_search_result(jobs, data_provider, warnings, challenge_detected)
        return self._capture_search_result(result)

    def last_live_provider(self) -> Optional[str]:
        return self._last_live_provider

    def legacy_backend_health(self) -> Tuple[bool, str, str]:
        now = datetime.utcnow()
        cache = self._legacy_health_cache
        if cache and self._legacy_health_checked_at and now - self._legacy_health_checked_at < self.LEGACY_HEALTH_TTL:
            result = cache
        else:
            result = self._legacy_backend_search("", "全国", limit=1)
            self._legacy_health_cache = result
            self._legacy_health_checked_at = now
        self._capture_search_result(result)
        return _has_live_jobs(result.jobs), result.provider or "legacy_backend", result.warning

    def _legacy_backend_search(self, keyword: str, city: str, limit: int) -> SearchResult:
        if not self.desktop_backend_url:
            return SearchResult(jobs=[], provider="legacy_backend", warning="legacy backend URL not configured")
        url = (
            f"{self.desktop_backend_url}/api/jobs/search"
            f"?keywords={quote_plus(keyword)}&location={quote_plus(city)}&limit={limit}"
        )
        try:
            payload = _http_get_json(url, timeout=25)
        except Exception as exc:
            return SearchResult(jobs=[], provider="legacy_backend", warning=f"legacy backend request failed: {exc}")

        jobs = payload.get("jobs") or []
        normalized: List[Dict[str, Any]] = []
        for index, row in enumerate(jobs, 1):
            normalized.append(
                {
                    "id": row.get("id") or f"legacy_{index}",
                    "title": row.get("title") or "",
                    "company": row.get("company") or "",
                    "salary": row.get("salary") or "",
                    "location": row.get("location") or city,
                    "experience": row.get("experience") or "",
                    "education": row.get("education") or "",
                    "description": row.get("description") or "",
                    "platform": row.get("platform") or "",
                    "link": row.get("link") or row.get("url") or "",
                    "provider": row.get("provider") or payload.get("provider_mode") or "legacy_backend",
                    "source": "legacy_backend",
                }
            )
        provider = _derive_reported_provider(normalized, str(payload.get("provider_mode") or "legacy_backend"))
        warning = _sanitize_provider_warning(provider, str(payload.get("warning") or payload.get("code") or ""))
        return SearchResult(jobs=_dedupe_jobs(normalized)[:limit], provider=provider, warning=str(warning or ""))

    def readiness_status(self, *, openclaw_status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if openclaw_status and openclaw_status.get("available"):
            return {"provider": "openclaw", "warning": "", "sample_count": None}

        if service_is_available():
            return {"provider": "desktop_real_job_service", "warning": "", "sample_count": None}

        legacy = self._legacy_backend_search("Python", "Shanghai", 1)
        reported_provider = _derive_reported_provider(legacy.jobs, legacy.provider)
        if _has_live_jobs(legacy.jobs):
            return {
                "provider": reported_provider,
                "warning": legacy.warning,
                "sample_count": len(legacy.jobs),
            }

        return {
            "provider": "fallback",
            "warning": legacy.warning or "live provider currently unavailable",
            "sample_count": len(legacy.jobs) or None,
        }

    def search_jobs(self, keyword: str, city: str, limit: int = 20) -> SearchResult:
        safe_limit = max(1, min(int(limit or 20), 200))
        warning_contexts: List[str] = []
        challenge_detected = False

        def _record_challenge() -> None:
            nonlocal challenge_detected
            if not challenge_detected:
                challenge_detected = True
                warning_contexts.append(
                    "OpenClaw session is blocked by Boss verification. Complete the challenge in the visible browser and retry."
                )

        openclaw_provider = _load_openclaw_provider()
        if openclaw_provider is not None:
            try:
                health = openclaw_provider.health_check()
                if health.get("available"):
                    base_module = importlib.import_module("app.services.job_providers.base")
                    params_cls = getattr(base_module, "JobSearchParams")
                    jobs = openclaw_provider.search_jobs(
                        params_cls(keywords=[keyword] if keyword else [], location=city, limit=safe_limit)
                    )
                    if jobs:
                        return self._finalize_and_record(jobs, "openclaw", warning_contexts, challenge_detected)
                    if _openclaw_challenge_state(openclaw_provider):
                        _record_challenge()
                else:
                    message = str(health.get("message") or "").strip()
                    if message:
                        warning_contexts.append(f"OpenClaw unavailable: {message}")
            except Exception as exc:
                message = str(exc)
                if _is_challenge_message(message) or _openclaw_challenge_state(openclaw_provider):
                    _record_challenge()
                else:
                    warning_contexts.append(f"OpenClaw search failed: {message}")
                logger.warning("OpenClaw provider search failed, continuing fallback chain: %s", exc, exc_info=True)
        else:
            warning_contexts.append("OpenClaw provider unavailable.")

        service = _load_real_job_service()
        if service is not None:
            try:
                jobs = service.search_jobs(
                    keywords=[keyword] if keyword else [],
                    location=city,
                    limit=safe_limit,
                )
                return self._finalize_and_record(jobs, "desktop_real_job_service", warning_contexts, challenge_detected)
            except Exception as exc:
                message = str(exc)
                warning_contexts.append(f"Desktop real job service error: {message}")
                logger.warning(
                    "RealJobService search failed, deferring to real web discovery stage: %s",
                    exc,
                    exc_info=True,
                )
        else:
            warning_contexts.append("Desktop real job service unavailable.")

        web_jobs, web_provider, discovery_warning = _real_web_discovery(keyword, city, safe_limit)
        if discovery_warning:
            warning_contexts.append(discovery_warning)
        if web_jobs:
            return self._finalize_and_record(web_jobs, web_provider, warning_contexts, challenge_detected)

        legacy = self._legacy_backend_search(keyword, city, safe_limit)
        if legacy.warning:
            warning_contexts.append(legacy.warning)
        if legacy.jobs:
            return self._finalize_and_record(
                legacy.jobs,
                legacy.provider or "legacy_backend",
                warning_contexts,
                challenge_detected,
            )

        warning_contexts.append("Real web discovery did not yield any live listings under the requested scopes.")
        warning_contexts.append("Fallback templates generated to keep the experience stable.")
        fallback_jobs = _fallback_jobs([keyword] if keyword else [], city, safe_limit)
        return self._finalize_and_record(fallback_jobs, "fallback", warning_contexts, challenge_detected)


def list_real_jobs(
    *,
    keywords: Optional[Sequence[str]] = None,
    location: Optional[str] = None,
    salary_min: Optional[int] = None,
    experience: Optional[str] = None,
    limit: int = 20,
    progress_callback=None,
) -> List[Dict[str, Any]]:
    """Return the most realistic job list available for the provided filters."""

    safe_limit = max(1, min(int(limit), 200)) if limit else 20
    normalized_keywords = _normalize_keywords(keywords)
    service = _load_real_job_service()
    if service:
        try:
            return service.search_jobs(
                keywords=normalized_keywords,
                location=location,
                salary_min=salary_min,
                experience=experience,
                limit=safe_limit,
                progress_callback=progress_callback,
            )
        except Exception as exc:
            logger.warning("RealJobService search failed, falling back to fallback generator: %s", exc, exc_info=True)

    return _fallback_jobs(
        keywords=normalized_keywords,
        location=location,
        limit=safe_limit,
    )


def _fallback_jobs(keywords: Sequence[str], location: Optional[str], limit: int) -> List[Dict[str, Any]]:
    seed = _fallback_seed(keywords, location, limit)
    rng = random.Random(seed)
    jobs: List[Dict[str, Any]] = []
    for index in range(limit):
        template = rng.choice(_FALLBACK_TEMPLATES)
        company = rng.choice(_FALLBACK_COMPANIES)
        location_choice = location or rng.choice(_FALLBACK_LOCATIONS)
        title = template["title"]
        if keywords:
            highlight = keywords[0]
            if highlight and highlight.lower() not in title.lower():
                title = f"{highlight.title()} {title}"
        salary = rng.choice(template["salary_range"])
        publish_date = (datetime.utcnow() - timedelta(days=rng.randint(0, 7))).strftime("%Y-%m-%d")
        match_score = min(100, 55 + rng.randint(0, 30) + (5 if keywords else 0))
        job = {
            "id": f"bridge_{seed}_{index}",
            "title": title,
            "company": company,
            "salary": salary,
            "location": location_choice,
            "experience": rng.choice(["2+ years", "3+ years", "5+ years"]),
            "education": rng.choice(["Bachelor", "Master"]),
            "requirements": template["skills"],
            "description": template["description"],
            "platform": template["platform"],
            "link": f"https://www.zhipin.com/web/geek/job?query={quote_plus(title + ' ' + company)}",
            "publish_date": publish_date,
            "company_category": rng.choice(["Global Tech", "Fintech", "Logistics", "AI Labs"]),
            "company_size": rng.choice(["200-500", "500-1000", "1000-3000", "3000+"]),
            "company_type": rng.choice(["Product", "Platform", "Finance", "Service"]),
            "welfare": rng.sample(_FALLBACK_BENEFITS, k=min(len(_FALLBACK_BENEFITS), 4)),
            "match_score": match_score,
            "match_percentage": min(100, match_score + rng.randint(0, 10)),
            "view_count": rng.randint(120, 3000),
            "apply_count": rng.randint(8, 450),
            "provider": "fallback",
            "source": "bridge",
        }
        jobs.append(job)
    return jobs
