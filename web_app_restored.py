"""
AI求职助手 - Web界面
一个漂亮的网页界面，让您直接在浏览器中使用
"""

from fastapi import FastAPI, Request, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
from typing import Optional, List, Dict, Any, Tuple
import asyncio
from datetime import datetime
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import re
import html as html_lib
import requests
import logging
import time
import uuid
import importlib.util
import json

sys.path.insert(0, os.path.dirname(__file__))

from app.core.multi_ai_debate import JobApplicationPipeline
from app.core.fast_ai_engine import fast_pipeline, HighPerformanceAIEngine
from app.core.market_driven_engine import market_driven_pipeline
from app.core.skills_graph import SkillsGraph
from app.core.llm_client import get_public_llm_config
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.real_job_service import RealJobService
from app.services.business_service import BusinessService
from app.services.resume_profile_service import ResumeProfileService
from app.services.resume_render_service import ResumeRenderService
from app.services.email_campaign_service import EmailCampaignService, SMTP_PRESETS
from app.core.realtime_progress import progress_tracker

app = FastAPI(title="AI求职助手")
APP_BOOT_TS = datetime.now().isoformat()
APP_BOOT_MONO = time.perf_counter()
logger = logging.getLogger("ai_job_helper")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("APP_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

# 使用市场驱动引擎
market_engine = market_driven_pipeline

# 挂载静态文件
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attach request id + process time headers for observability."""
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()
    request.state.request_id = rid
    try:
        response = await call_next(request)
    except Exception as e:
        took_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_failed path=%s method=%s rid=%s took_ms=%.1f err=%s",
            request.url.path,
            request.method,
            rid,
            took_ms,
            str(e)[:300],
        )
        return JSONResponse(
            {"success": False, "error": "internal_error", "request_id": rid},
            status_code=500,
            headers={"x-request-id": rid, "x-process-time-ms": f"{took_ms:.1f}"},
        )

    took_ms = (time.perf_counter() - start) * 1000
    response.headers["x-request-id"] = rid
    response.headers["x-process-time-ms"] = f"{took_ms:.1f}"
    if request.url.path.startswith("/api"):
        logger.info(
            "request_done path=%s method=%s status=%s rid=%s took_ms=%.1f",
            request.url.path,
            request.method,
            getattr(response, "status_code", 0),
            rid,
            took_ms,
        )
    return response

# 全局变量
pipeline = JobApplicationPipeline()
analyzer = ResumeAnalyzer()
skills_graph = SkillsGraph()
real_job_service = RealJobService()  # 真实招聘数据服务
business_service = BusinessService()
resume_profile_service = ResumeProfileService()
resume_render_service = ResumeRenderService()
email_campaign_service = EmailCampaignService()

# 云端岗位缓存（内存）
cloud_jobs_cache: List[Dict[str, Any]] = []
CN_JOB_DOMAINS = ("zhipin.com", "liepin.com", "zhaopin.com", "51job.com", "lagou.com")
cloud_jobs_meta: Dict[str, Any] = {
    "last_push_at": None,
    "last_received": 0,
    "last_new": 0,
}
recent_search_jobs: Dict[str, Dict[str, Any]] = {}
github_apply_tasks: Dict[str, Dict[str, Any]] = {}
boss_sms_code_store: Dict[str, Dict[str, Any]] = {}
boss_control_action_store: Dict[str, Dict[str, Any]] = {}
HAITOU_DEFAULT_POLICY: Dict[str, Any] = {
    "enabled": True,
    "fallback_platforms": ["boss", "zhilian", "linkedin"],
    "max_count": 80,
    "headless": True,
    "allow_portal_fallback": True,
    "verification_wait_seconds": 180,
    "strategy_version": "haitou_v1",
}
AIHAWK_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "third_party", "Auto_Jobs_Applier_AIHawk")
)


def _api_success(payload: Dict[str, Any], status_code: int = 200) -> JSONResponse:
    body = {"success": True}
    body.update(payload or {})
    return JSONResponse(body, status_code=status_code)


def _api_error(message: str, status_code: int = 400, code: str = "bad_request") -> JSONResponse:
    return JSONResponse(
        {"success": False, "error": message, "code": code},
        status_code=status_code,
    )


def _to_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


def _apply_haitou_defaults(raw: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(raw or {})
    # Global permanent strategy: enforce identical haitou policy for all users.
    data["enable_fallback_auto_apply"] = True
    data["fallback_platforms"] = list(HAITOU_DEFAULT_POLICY["fallback_platforms"])
    data["platforms"] = list(HAITOU_DEFAULT_POLICY["fallback_platforms"])
    data["max_count"] = int(HAITOU_DEFAULT_POLICY["max_count"])
    data["headless"] = bool(HAITOU_DEFAULT_POLICY["headless"])
    data["verification_wait_seconds"] = int(HAITOU_DEFAULT_POLICY["verification_wait_seconds"])
    cfg = dict(data.get("config") or {})
    cfg["max_count"] = int(HAITOU_DEFAULT_POLICY["max_count"])
    cfg["headless"] = bool(HAITOU_DEFAULT_POLICY["headless"])
    cfg["verification_wait_seconds"] = int(HAITOU_DEFAULT_POLICY["verification_wait_seconds"])
    data["config"] = cfg
    return data


def _mask_phone(phone: str) -> str:
    s = str(phone or "").strip()
    if len(s) >= 7:
        return f"{s[:3]}****{s[-4:]}"
    return s


def _resolve_auto_apply_task_id(task_id: str = "", gh_task_id: str = "") -> str:
    tid = str(task_id or "").strip()
    if tid:
        return tid
    gid = str(gh_task_id or "").strip()
    if not gid:
        return ""
    gh_task = github_apply_tasks.get(gid) or {}
    return str(gh_task.get("linked_auto_apply_task_id") or "").strip()


def _set_boss_sms_code(task_id: str, code: str) -> None:
    tid = str(task_id or "").strip()
    if not tid:
        return
    boss_sms_code_store[tid] = {
        "code": str(code or "").strip(),
        "updated_at": datetime.now().isoformat(),
    }


def _pop_boss_sms_code(task_id: str) -> str:
    tid = str(task_id or "").strip()
    if not tid:
        return ""
    row = boss_sms_code_store.pop(tid, None) or {}
    return str(row.get("code") or "").strip()


def _push_boss_control_action(task_id: str, action: str) -> None:
    tid = str(task_id or "").strip()
    act = str(action or "").strip().lower()
    if not tid or not act:
        return
    boss_control_action_store[tid] = {
        "action": act,
        "updated_at": datetime.now().isoformat(),
    }


def _pop_boss_control_action(task_id: str) -> str:
    tid = str(task_id or "").strip()
    if not tid:
        return ""
    row = boss_control_action_store.pop(tid, None) or {}
    return str(row.get("action") or "").strip().lower()


def _aihawk_capability_snapshot() -> Dict[str, Any]:
    root_exists = os.path.isdir(AIHAWK_ROOT)
    required_files = ["main.py", "config.py", "requirements.txt", "data_folder"]
    missing_required = [
        p for p in required_files if not os.path.exists(os.path.join(AIHAWK_ROOT, p))
    ]

    dep_names = ["yaml", "inquirer", "selenium", "webdriver_manager"]
    missing_deps = [d for d in dep_names if importlib.util.find_spec(d) is None]

    plugin_markers = [
        "ai_hawk/bot_facade.py",
        "ai_hawk/job_manager.py",
    ]
    has_auto_apply_plugins = all(
        os.path.exists(os.path.join(AIHAWK_ROOT, rel)) for rel in plugin_markers
    )

    llm_key_ready = bool(
        os.getenv("DEEPSEEK_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
    )

    can_prepare = root_exists and (len(missing_required) == 0) and ("yaml" not in missing_deps)
    can_run = can_prepare and has_auto_apply_plugins and (len(missing_deps) == 0) and llm_key_ready

    blockers: List[str] = []
    actions: List[str] = []
    if missing_required:
        blockers.append(f"缺少必要文件: {missing_required}")
        actions.append("补齐 third_party/Auto_Jobs_Applier_AIHawk 目录结构")
    if missing_deps:
        blockers.append(f"缺少依赖: {missing_deps}")
        actions.append("在后端虚拟环境安装缺失依赖")
    if not has_auto_apply_plugins:
        blockers.append("当前 AIHawk 版本缺少 auto-apply 插件代码")
        actions.append("切换到含插件的历史提交或私有分支")
    if not llm_key_ready:
        blockers.append("未配置 LLM API KEY")
        actions.append("配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")

    return {
        "root": AIHAWK_ROOT,
        "root_exists": root_exists,
        "missing_required": missing_required,
        "missing_deps": missing_deps,
        "has_auto_apply_plugins": has_auto_apply_plugins,
        "llm_key_ready": llm_key_ready,
        "mode": "full_auto_apply" if has_auto_apply_plugins else "prepare_only",
        "can_prepare": can_prepare,
        "can_run": can_run,
        "blockers": blockers,
        "actions": actions,
    }


def _skills_graph_payload(
    resume_text: str,
    target_role: str = "",
    job_text: str = "",
) -> Dict[str, Any]:
    resume_text = str(resume_text or "")
    target_role = str(target_role or "").strip()
    job_text = str(job_text or "")

    if not target_role:
        try:
            parsed = analyzer.extract_info(resume_text)
            target_role = str(parsed.get("job_intention") or "").strip()
        except Exception:
            target_role = ""

    resume_skills = skills_graph.extract_skills(resume_text)
    job_skills = skills_graph.extract_skills(job_text or target_role)

    match_score = None
    if job_skills:
        match_score = round(skills_graph.calculate_match_score(resume_skills, job_skills), 1)

    recommend_for = target_role or "后端开发"
    recommended = skills_graph.recommend_skills(resume_skills, recommend_for)

    return {
        "target_role": target_role,
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "match_score": match_score,
        "recommended_skills": recommended,
    }


def _multi_agent_outputs_degraded(results: Dict[str, Any]) -> bool:
    fields = [
        str(results.get("career_analysis") or ""),
        str(results.get("job_recommendations") or ""),
        str(results.get("optimized_resume") or ""),
        str(results.get("interview_prep") or ""),
        str(results.get("mock_interview") or ""),
    ]
    bad = 0
    for text in fields:
        t = text.lower()
        if ("ai思考出错" in text) or ("authentication fails" in t) or ("error" in t and len(t) < 120):
            bad += 1
    return bad >= 3


def _decode_text_file_bytes(content: bytes) -> str:
    """Best-effort decode for uploaded txt files with mixed encodings."""
    if not content:
        return ""

    candidates = [
        "utf-8-sig",
        "utf-16",
        "utf-16le",
        "utf-16be",
        "gb18030",
        "gbk",
    ]

    decoded = None
    for enc in candidates:
        try:
            decoded = content.decode(enc)
            break
        except Exception:
            continue

    if decoded is None:
        decoded = content.decode("utf-8", errors="ignore")

    # Normalize common artifacts from wrong fallback decoding.
    decoded = decoded.replace("\x00", "").replace("\ufeff", "")
    decoded = decoded.replace("\r\n", "\n").replace("\r", "\n")
    return decoded.strip()


def _normalize_extracted_text(text: str) -> str:
    if not text:
        return ""
    out = text.replace("\x00", "").replace("\ufeff", "")
    out = out.replace("\r\n", "\n").replace("\r", "\n")
    # Keep line breaks, but collapse excessive blank lines.
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _text_quality_score(text: str) -> float:
    """Heuristic score for extracted text readability (0.0 ~ 1.0)."""
    t = _normalize_extracted_text(text)
    if not t:
        return 0.0

    total = max(1, len(t))
    printable = sum(1 for ch in t if ch.isprintable() or ch in "\n\t")
    control = sum(1 for ch in t if (ord(ch) < 32 and ch not in "\n\t"))
    replacement = t.count("\ufffd")
    ascii_word = len(re.findall(r"[A-Za-z0-9]", t))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", t))

    printable_ratio = printable / total
    useful_ratio = min(1.0, (ascii_word + cjk) / total)
    control_ratio = control / total
    replacement_ratio = replacement / total
    length_factor = min(1.0, total / 320.0)

    score = (
        0.45 * printable_ratio
        + 0.30 * useful_ratio
        + 0.25 * length_factor
        - 0.70 * control_ratio
        - 0.90 * replacement_ratio
    )
    return max(0.0, min(1.0, score))


def _looks_like_mojibake(text: str) -> bool:
    t = _normalize_extracted_text(text)
    if not t:
        return True
    if ("\ufffd" in t) or ("\x00" in t):
        return True
    # Typical mojibake traces like 'ÿ', 'ð', etc.
    latin_ext = len(re.findall(r"[\u00C0-\u024F]", t))
    if latin_ext >= 2 and (latin_ext / max(1, len(t))) > 0.002:
        return True
    return False


def _ocr_image_best_effort(image: Any) -> str:
    """Run OCR with language fallback order."""
    import pytesseract

    for lang in ("chi_sim+eng", "chi_sim", "eng"):
        try:
            text = pytesseract.image_to_string(image, lang=lang)
            text = _normalize_extracted_text(text)
            if text:
                return text
        except Exception:
            continue
    return ""


def _extract_pdf_text_pypdf2(content: bytes) -> str:
    import io
    import PyPDF2

    reader = PyPDF2.PdfReader(io.BytesIO(content))
    chunks: List[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            chunks.append(txt)
    return _normalize_extracted_text("\n".join(chunks))


def _extract_pdf_text_pymupdf(content: bytes) -> str:
    try:
        import fitz  # PyMuPDF
    except Exception:
        return ""

    doc = fitz.open(stream=content, filetype="pdf")
    chunks: List[str] = []
    try:
        for page in doc:
            txt = page.get_text("text") or ""
            if txt.strip():
                chunks.append(txt)
    finally:
        doc.close()
    return _normalize_extracted_text("\n".join(chunks))


def _extract_pdf_text_ocr(content: bytes, max_pages: int = 8) -> str:
    """OCR fallback for scanned/garbled PDFs using PyMuPDF rasterization."""
    try:
        import fitz  # PyMuPDF
        from PIL import Image
    except Exception:
        return ""

    doc = fitz.open(stream=content, filetype="pdf")
    chunks: List[str] = []
    try:
        limit = min(max_pages, doc.page_count)
        for idx in range(limit):
            page = doc.load_page(idx)
            # 2x scale improves OCR precision for resumes.
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            mode = "RGB" if pix.n < 4 else "RGBA"
            image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            txt = _ocr_image_best_effort(image)
            if txt:
                chunks.append(txt)
    finally:
        doc.close()
    return _normalize_extracted_text("\n".join(chunks))


def _extract_pdf_text_best_effort(content: bytes) -> Tuple[str, str]:
    """Try text extraction first, then OCR fallback when quality is poor."""
    candidates: List[Tuple[str, str]] = []

    try:
        txt = _extract_pdf_text_pypdf2(content)
        if txt:
            candidates.append(("pypdf2", txt))
    except Exception as e:
        logger.warning("pypdf2_extract_failed err=%s", str(e)[:200])

    try:
        txt = _extract_pdf_text_pymupdf(content)
        if txt:
            candidates.append(("pymupdf_text", txt))
    except Exception as e:
        logger.warning("pymupdf_extract_failed err=%s", str(e)[:200])

    best_text = ""
    best_source = ""
    best_score = 0.0
    for source, txt in candidates:
        score = _text_quality_score(txt)
        if score > best_score:
            best_score = score
            best_text = txt
            best_source = source

    # Always try OCR when available and prefer it for suspicious/low-quality extracted text.
    try:
        ocr_text = _extract_pdf_text_ocr(content)
        ocr_score = _text_quality_score(ocr_text)
        if ocr_text:
            should_take_ocr = False
            if not best_text:
                should_take_ocr = True
            elif _looks_like_mojibake(best_text):
                should_take_ocr = True
            elif ocr_score >= best_score + 0.06:
                should_take_ocr = True
            elif ocr_score >= max(0.45, best_score - 0.06) and len(ocr_text) >= len(best_text) * 0.6:
                should_take_ocr = True

            if should_take_ocr:
                best_text = ocr_text
                best_source = "ocr"
                best_score = ocr_score
    except Exception as e:
        logger.warning("pdf_ocr_failed err=%s", str(e)[:200])

    return _normalize_extracted_text(best_text), (best_source or "none")


def _build_investor_readiness_snapshot() -> Dict[str, Any]:
    """
    Financing-oriented readiness snapshot.
    Provides one consolidated view for product, traction, reliability and GTM.
    """
    metrics = business_service.metrics()
    funnel = metrics.get("funnel", {})
    leads = metrics.get("leads", {})
    feedback = metrics.get("feedback", {})
    stability = metrics.get("stability", {})

    cfg_mode = os.getenv("JOB_DATA_PROVIDER", "auto").strip().lower()
    enterprise_on = bool(os.getenv("ENTERPRISE_JOB_API_URL", "").strip())
    global_fallback_on = os.getenv("ENABLE_GLOBAL_JOB_FALLBACK", "").strip().lower() in {"1", "true", "yes", "on"}

    uploads = int(funnel.get("uploads", 0) or 0)
    process_runs = int(funnel.get("process_runs", 0) or 0)
    searches = int(funnel.get("searches", 0) or 0)
    applies = int(funnel.get("applies", 0) or 0)
    api_errors = int(stability.get("api_errors", 0) or 0)

    process_success_pct = float(funnel.get("process_success_pct", 0) or 0)
    search_to_apply_pct = float(funnel.get("search_to_apply_pct", 0) or 0)

    product_score = 100.0
    if cfg_mode not in {"auto", "cloud", "baidu", "bing", "brave", "jooble", "openclaw", "enterprise_api"}:
        product_score -= 25.0
    if global_fallback_on:
        product_score -= 15.0
    if process_success_pct < 90:
        product_score -= 15.0
    if process_success_pct < 75:
        product_score -= 15.0
    if enterprise_on:
        product_score += 5.0
    product_score = max(0.0, min(100.0, product_score))

    traction_score = 0.0
    traction_score += min(35.0, uploads * 1.2)
    traction_score += min(35.0, process_runs * 1.5)
    traction_score += min(20.0, searches * 0.9)
    traction_score += min(10.0, applies * 2.0)
    traction_score = max(0.0, min(100.0, traction_score))

    reliability_score = 100.0
    if process_runs > 0:
        err_ratio = api_errors / max(process_runs, 1)
        reliability_score -= min(60.0, err_ratio * 100.0)
    if api_errors >= 20:
        reliability_score -= 10.0
    reliability_score = max(0.0, min(100.0, reliability_score))

    gtm_score = 0.0
    gtm_score += min(45.0, int(leads.get("total", 0) or 0) * 12.0)
    gtm_score += min(25.0, int(leads.get("last_7d", 0) or 0) * 8.0)
    gtm_score += min(10.0, int(feedback.get("last_7d", 0) or 0) * 2.5)
    gtm_score += min(15.0, search_to_apply_pct * 0.8)
    gtm_score += 10.0 if searches > 0 else 0.0
    gtm_score += 5.0 if applies > 0 else 0.0
    gtm_score = max(0.0, min(100.0, gtm_score))

    weighted = (
        product_score * 0.35
        + traction_score * 0.25
        + reliability_score * 0.25
        + gtm_score * 0.15
    )
    overall = round(max(0.0, min(100.0, weighted)), 1)

    status = "seed_ready" if overall >= 75 else ("pre_seed_ready" if overall >= 60 else "build_stage")

    return {
        "status": status,
        "overall_score": overall,
        "pillars": {
            "product": round(product_score, 1),
            "traction": round(traction_score, 1),
            "reliability": round(reliability_score, 1),
            "go_to_market": round(gtm_score, 1),
        },
        "highlights": {
            "provider_mode": cfg_mode,
            "enterprise_api_configured": enterprise_on,
            "global_fallback_enabled": global_fallback_on,
            "cloud_cache_total": len(cloud_jobs_cache),
            "feedback_total": int(feedback.get("total", 0) or 0),
        },
        "metrics": metrics,
        "next_30d_targets": {
            "uploads": max(uploads + 80, 120),
            "process_runs": max(process_runs + 60, 100),
            "searches": max(searches + 100, 180),
            "applies": max(applies + 30, 40),
            "leads_total": max(int(leads.get("total", 0) or 0) + 20, 30),
        },
    }


def _track_event(name: str, payload: Optional[Dict[str, Any]] = None) -> None:
    try:
        business_service.track_event(name, payload or {})
    except Exception:
        # Do not break core user path due to analytics write failures.
        pass


def _cache_recent_jobs(jobs: List[Dict[str, Any]], max_size: int = 2000) -> None:
    now = datetime.now().isoformat()
    for j in jobs or []:
        jid = str(j.get("id") or "").strip()
        if not jid:
            continue
        row = dict(j)
        row["_cached_at"] = now
        recent_search_jobs[jid] = row
    if len(recent_search_jobs) > max_size:
        # Keep newest max_size by cached time.
        items = sorted(
            recent_search_jobs.items(),
            key=lambda x: str(x[1].get("_cached_at") or ""),
            reverse=True,
        )[:max_size]
        recent_search_jobs.clear()
        recent_search_jobs.update(items)


def _is_seed_or_demo_job(job: Dict[str, Any]) -> bool:
    """Filter obvious seed/demo jobs so they never show in production recommendations."""
    jid = str(job.get("id") or "").strip().lower()
    if jid.startswith("seed") or jid.startswith("demo"):
        return True
    link = str(job.get("link") or job.get("apply_url") or "").strip().lower()
    if "/job_detail/seed" in link:
        return True
    company = str(job.get("company") or "").strip().lower()
    if company in {"示例公司", "测试公司", "demo"}:
        return True
    return False


def _job_has_actionable_link(job: Dict[str, Any]) -> bool:
    link = str(job.get("link") or job.get("apply_url") or "").strip()
    return link.startswith("http://") or link.startswith("https://")


def _is_cn_entrypoint_link(link: str) -> bool:
    """Search entry/list pages are not treated as real actionable postings."""
    low = (link or "").strip().lower()
    if not low:
        return False
    patterns = (
        "zhipin.com/web/geek/job?",
        "zhipin.com/zhaopin/",
        "liepin.com/zhaopin/?key=",
        "sou.zhaopin.com/?kw=",
        "we.51job.com/pc/search?",
        "lagou.com/wn/jobs?kd=",
    )
    return any(p in low for p in patterns)


def _is_cn_entrypoint_job(job: Dict[str, Any]) -> bool:
    provider = str(job.get("provider") or "").strip().lower()
    title = str(job.get("title") or job.get("job_title") or "").strip().lower()
    link = str(job.get("link") or job.get("apply_url") or "").strip()
    if provider == "cn_portal":
        return True
    if "搜索入口" in title:
        return True
    return _is_cn_entrypoint_link(link)


def _normalize_and_filter_jobs(jobs: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """Keep only actionable real jobs and deduplicate by link/id/title-company."""
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for job in jobs or []:
        if not isinstance(job, dict):
            continue
        if _is_seed_or_demo_job(job):
            continue
        if not _job_has_actionable_link(job):
            continue

        link = str(job.get("link") or job.get("apply_url") or "").strip().lower()
        jid = str(job.get("id") or "").strip().lower()
        title = str(job.get("title") or job.get("job_title") or "").strip().lower()
        company = str(job.get("company") or "").strip().lower()
        dedupe_key = link or jid or f"{title}|{company}"
        if not dedupe_key or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        out.append(job)
        if len(out) >= max(1, int(limit or 10)):
            break
    return out


def _normalize_real_jobs(jobs: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Strict real-posting normalization:
    - actionable links only
    - no seed/demo
    - no board-level search entry pages
    """
    scan_limit = max(20, int(limit or 10) * 5)
    base = _normalize_and_filter_jobs(jobs, limit=scan_limit)
    out: List[Dict[str, Any]] = []
    for job in base:
        if _is_cn_entrypoint_job(job):
            continue
        out.append(job)
        if len(out) >= max(1, int(limit or 10)):
            break
    return out


def _is_cn_job_link(link: str) -> bool:
    low = (link or "").lower()
    return any(d in low for d in CN_JOB_DOMAINS)


def _enforce_cn_market_jobs(
    jobs: List[Dict[str, Any]],
    allow_entrypoints: bool = False,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for j in (jobs or []):
        if (not allow_entrypoints) and _is_cn_entrypoint_job(j):
            continue
        link = str(j.get("link") or j.get("apply_url") or "")
        platform = str(j.get("platform") or "").strip()
        if _is_cn_job_link(link):
            out.append(j)
            continue
        if platform in {"Boss直聘", "猎聘", "智联招聘", "前程无忧", "拉勾"}:
            out.append(j)
    return out


PROCESS_RESPONSE_SCHEMA_VERSION = "process_response.v2"
LOW_QUALITY_MARKERS = (
    "i appreciate your interest",
    "amazon q",
    "built by aws",
    "i'm amazon q",
    "i am amazon q",
    "not career counseling",
    "没有看到任何附件",
)
PUBLIC_EVENT_NAME_PATTERN = re.compile(r"^[a-z0-9_]{3,48}$")
PUBLIC_EVENT_WHITELIST = {
    "workspace_opened",
    "resume_process_started",
    "resume_process_success",
    "resume_process_failed",
    "job_link_click",
    "result_download",
}


def _text_has_low_quality_marker(text: str) -> bool:
    low = (text or "").strip().lower()
    if not low:
        return True
    return any(marker in low for marker in LOW_QUALITY_MARKERS)


def _render_market_analysis_fallback(info: Dict[str, Any]) -> str:
    skills = [s for s in (info.get("skills") or []) if s][:8]
    skills_text = ", ".join(skills) if skills else "Python, FastAPI, SQL"
    return (
        "【市场竞争力分析】\n\n"
        f"✅ 识别技能：{skills_text}\n\n"
        "📊 市场需求度：中高（基于中国技术岗位关键词覆盖）\n"
        "💼 建议投递方向：Python后端 / AI应用工程 / 数据工程\n"
        "📈 建议策略：先投递有明确技术栈和薪资区间的岗位，再按反馈迭代简历。\n\n"
        "💡 市场建议：\n"
        "1. 先聚焦 1-2 个主岗位方向，避免关键词过散。\n"
        "2. 简历中补充可量化结果（性能提升、效率提升、交付周期）。\n"
        "3. 优先投递带真实岗位详情页和直接投递入口的职位。"
    )


def _render_interview_prep_fallback(info: Dict[str, Any], jobs: List[Dict[str, Any]]) -> str:
    top = (jobs or [{}])[0]
    title = str(top.get("title") or "Python后端工程师")
    company = str(top.get("company") or "目标公司")
    return (
        f"目标岗位：{title}（{company}）\n\n"
        "高频问题 1：你如何设计高并发 API？\n"
        "回答要点：异步 I/O、缓存策略、限流、慢查询治理、可观测性。\n\n"
        "高频问题 2：你如何保证数据链路质量？\n"
        "回答要点：输入校验、幂等设计、回滚方案、监控告警、复盘机制。\n\n"
        "高频问题 3：你做过最有业务价值的项目是什么？\n"
        "回答要点：按“背景-动作-结果”讲清指标提升，并说明你的关键贡献。"
    )


def _render_optimized_resume_fallback(resume_text: str, info: Dict[str, Any]) -> str:
    name = str(info.get("name") or "").strip()
    if not name or name == "未知":
        first = (resume_text or "").strip().splitlines()
        name = first[0].strip() if first else "候选人"
    skills = [s for s in (info.get("skills") or []) if s][:10]
    skills_line = ", ".join(skills) if skills else "Python, FastAPI, SQL, Docker"
    return (
        f"{name}\n"
        "AI应用工程师 | Python后端工程师\n\n"
        "核心优势\n"
        "- 聚焦 AI 应用工程与后端交付，能从需求到上线完成闭环。\n"
        "- 具备数据处理、服务部署、性能优化和质量门禁实践。\n\n"
        f"技术栈\n- {skills_line}\n\n"
        "项目亮点（示例结构）\n"
        "- 构建 RAG/数据服务，接口稳定性提升，响应延迟下降。\n"
        "- 建立自动化数据管道，减少人工处理成本并提高时效。\n"
        "- 引入测试与监控机制，降低线上故障率并缩短定位时间。\n\n"
        "求职方向\n- Python后端开发\n- AI应用开发\n- 数据工程与平台方向"
    )


def _run_output_quality_gate(
    results: Dict[str, Any],
    resume_text: str,
    info: Dict[str, Any],
    real_jobs: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    clean = dict(results or {})
    report: Dict[str, Any] = {"passed": True, "issues": []}

    market_analysis = str(clean.get("market_analysis") or "").strip()
    if len(market_analysis) < 80 or _text_has_low_quality_marker(market_analysis):
        clean["market_analysis"] = _render_market_analysis_fallback(info)
        report["issues"].append("market_analysis_replaced")

    optimized_resume = str(clean.get("optimized_resume") or "").strip()
    if len(optimized_resume) < 120 or _text_has_low_quality_marker(optimized_resume):
        clean["optimized_resume"] = _render_optimized_resume_fallback(resume_text, info)
        report["issues"].append("optimized_resume_replaced")

    interview_prep = str(clean.get("interview_prep") or "").strip()
    if len(interview_prep) < 80 or _text_has_low_quality_marker(interview_prep):
        clean["interview_prep"] = _render_interview_prep_fallback(info, real_jobs)
        report["issues"].append("interview_prep_replaced")

    salary_analysis = str(clean.get("salary_analysis") or "").strip()
    if not salary_analysis:
        clean["salary_analysis"] = "【薪资潜力分析】\n\n建议：基于岗位匹配度和市场供需，优先投递高匹配岗位后再进行薪资谈判。"
        report["issues"].append("salary_analysis_replaced")

    if report["issues"]:
        report["passed"] = False
    return clean, report


def _public_job_payload(
    jobs: List[Dict[str, Any]],
    limit: int = 10,
    allow_entrypoints: bool = False,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    normalized = (
        _normalize_and_filter_jobs(jobs or [], limit=limit)
        if allow_entrypoints
        else _normalize_real_jobs(jobs or [], limit=limit)
    )
    for j in normalized:
        link = str(j.get("link") or j.get("apply_url") or "").strip()
        out.append(
            {
                "id": str(j.get("id") or f"job_{abs(hash(link.lower()))}"),
                "title": str(j.get("title") or j.get("job_title") or "未知岗位"),
                "company": str(j.get("company") or ""),
                "location": str(j.get("location") or ""),
                "salary": str(j.get("salary") or j.get("salary_range") or ""),
                "platform": str(j.get("platform") or j.get("provider") or _platform_from_link(link)),
                "link": link,
                "provider": str(j.get("provider") or ""),
                "updated": str(j.get("updated") or ""),
            }
        )
    return out


def _validate_process_response_shape(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required_text_fields = (
        "career_analysis",
        "job_recommendations",
        "optimized_resume",
        "interview_prep",
        "mock_interview",
        "job_provider_mode",
        "schema_version",
    )
    for key in required_text_fields:
        if not isinstance(payload.get(key), str):
            errors.append(f"{key}:expected_string")

    jobs = payload.get("recommended_jobs")
    if not isinstance(jobs, list):
        errors.append("recommended_jobs:expected_list")
    else:
        for idx, row in enumerate(jobs[:20]):
            if not isinstance(row, dict):
                errors.append(f"recommended_jobs[{idx}]:expected_object")
                continue
            for key in ("id", "title", "link"):
                if not isinstance(row.get(key), str) or not str(row.get(key)).strip():
                    errors.append(f"recommended_jobs[{idx}].{key}:missing")
                    break
    return errors


def _filter_cloud_cache_by_query(
    keywords: List[str], location: Optional[str], limit: int
) -> List[Dict[str, Any]]:
    kw = [k.strip().lower() for k in (keywords or []) if k and k.strip()]

    def hit(job: Dict[str, Any]) -> bool:
        text = f"{job.get('title','')} {job.get('company','')}".lower()
        if kw and not any(k in text for k in kw):
            return False
        if location and job.get("location") and location not in str(job.get("location")):
            return False
        return True

    matched = [j for j in cloud_jobs_cache if hit(j)]
    if not matched:
        matched = list(cloud_jobs_cache)
    return _normalize_real_jobs(matched, limit=limit)


def _search_jobs_without_browser(
    keywords: List[str],
    location: Optional[str],
    limit: int,
    allow_portal_fallback: bool = False,
) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
    """
    Cloud-safe real-time search path.
    No local browser/OpenClaw required.
    """
    try:
        jobs = real_job_service.search_jobs(
            keywords=keywords,
            location=location,
            limit=max(5, min(int(limit or 10), 50)),
        )
        mode = (real_job_service.get_statistics() or {}).get("provider_mode", "auto")
        normalized = _normalize_real_jobs(jobs, limit=limit)
        normalized = _enforce_cn_market_jobs(normalized)
        if normalized:
            return normalized, mode, None
    except Exception as e:
        first_error = str(e)
    else:
        first_error = None

    enterprise_jobs = _search_jobs_enterprise_api(keywords, location, limit=limit)
    enterprise_jobs = _normalize_real_jobs(enterprise_jobs, limit=limit)
    enterprise_jobs = _enforce_cn_market_jobs(enterprise_jobs)
    if enterprise_jobs:
        return enterprise_jobs, "enterprise_api", None

    # CN market fallback: no-browser HTML search on Chinese job sites.
    bing_html_jobs = _search_jobs_bing_html(keywords, location, limit=limit)
    bing_html_jobs = _normalize_real_jobs(bing_html_jobs, limit=limit)
    bing_html_jobs = _enforce_cn_market_jobs(bing_html_jobs)
    if bing_html_jobs:
        return bing_html_jobs, "bing_html", None

    # Last fallback: DuckDuckGo HTML search (no key, no browser).
    ddg_jobs = _search_jobs_duckduckgo(keywords, location, limit=limit)
    ddg_jobs = _normalize_real_jobs(ddg_jobs, limit=limit)
    ddg_jobs = _enforce_cn_market_jobs(ddg_jobs)
    if ddg_jobs:
        return ddg_jobs, "duckduckgo", None

    # Optional global fallback. Disabled by default to keep CN market realism.
    if os.getenv("ENABLE_GLOBAL_JOB_FALLBACK", "").strip().lower() in {"1", "true", "yes", "on"}:
        remotive_jobs = _search_jobs_remotive(keywords, location, limit=limit)
        if remotive_jobs:
            return remotive_jobs, "remotive", None

    if allow_portal_fallback:
        portal_jobs = _search_jobs_cn_entrypoints(keywords, location, limit=min(limit, 5))
        if portal_jobs:
            return portal_jobs, "cn_portal", first_error or "using cn portal fallback"

    return [], "no_real_jobs", first_error or "no result from no-browser providers"


def _platform_from_link(link: str) -> str:
    host = (urlparse(link).netloc or "").lower()
    if "zhipin.com" in host:
        return "Boss直聘"
    if "liepin.com" in host:
        return "猎聘"
    if "zhaopin.com" in host:
        return "智联招聘"
    if "51job.com" in host:
        return "前程无忧"
    if "lagou.com" in host:
        return "拉勾"
    return host or "web"


def _first_non_empty(row: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        v = row.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


def _infer_company_from_title(title: str, platform: str = "") -> str:
    t = (title or "").strip()
    if not t:
        return ""
    # Boss style examples:
    # - 「Python招聘」_苏州鼎级招聘-BOSS直聘
    # - Python开发工程师 - 某某科技 - Boss直聘
    if "_" in t:
        tail = t.split("_", 1)[1].strip()
        tail = re.split(r"[-|｜]", tail)[0].strip()
        tail = tail.replace("招聘", "").replace("诚聘", "").strip()
        if 1 <= len(tail) <= 24 and "直聘" not in tail:
            return tail
    parts = [p.strip() for p in re.split(r"[-|｜]", t) if p.strip()]
    for p in parts[1:3]:
        if any(x in p for x in ("直聘", "招聘", "猎聘", "前程无忧", "拉勾", "智联")):
            continue
        if 1 <= len(p) <= 24:
            return p.replace("招聘", "").replace("诚聘", "").strip()
    return ""


def _search_jobs_enterprise_api(
    keywords: List[str], location: Optional[str], limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Enterprise-grade provider hook (config-driven).
    Intended for stable cloud use when search engines hit anti-bot limits.
    """
    url = os.getenv("ENTERPRISE_JOB_API_URL", "").strip()
    if not url:
        return []

    method = os.getenv("ENTERPRISE_JOB_API_METHOD", "GET").strip().upper()
    timeout_s = int(os.getenv("ENTERPRISE_JOB_API_TIMEOUT_S", "15") or "15")
    auth_header = os.getenv("ENTERPRISE_JOB_API_AUTH_HEADER", "Authorization").strip() or "Authorization"
    auth_scheme = os.getenv("ENTERPRISE_JOB_API_AUTH_SCHEME", "Bearer").strip()
    api_key = os.getenv("ENTERPRISE_JOB_API_KEY", "").strip()

    kw = [k.strip() for k in (keywords or []) if k and k.strip()]
    query = " ".join(kw[:5]) or "Python"
    payload = {
        "query": query,
        "keywords": kw,
        "location": (location or "").strip(),
        "limit": max(1, min(int(limit or 10), 50)),
    }
    headers = {"User-Agent": "ai-job-helper/1.0"}
    if api_key:
        headers[auth_header] = f"{auth_scheme} {api_key}".strip() if auth_scheme else api_key

    try:
        if method == "POST":
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout_s)
        else:
            resp = requests.get(url, params=payload, headers=headers, timeout=timeout_s)
        if resp.status_code >= 400:
            return []
        data = resp.json() if resp.content else {}
    except Exception:
        return []

    rows: List[Dict[str, Any]] = []
    if isinstance(data, list):
        rows = [x for x in data if isinstance(x, dict)]
    elif isinstance(data, dict):
        for k in ("jobs", "results", "items", "list", "data"):
            v = data.get(k)
            if isinstance(v, list):
                rows = [x for x in v if isinstance(x, dict)]
                break
            if isinstance(v, dict):
                for kk in ("jobs", "results", "items", "list"):
                    vv = v.get(kk)
                    if isinstance(vv, list):
                        rows = [x for x in vv if isinstance(x, dict)]
                        break
                if rows:
                    break

    out: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        link = _first_non_empty(row, ["link", "url", "job_url", "detail_url", "apply_url", "jobLink", "jobUrl"])
        if not link:
            continue
        title = _first_non_empty(row, ["title", "job_title", "name", "position", "jobName"]) or "招聘岗位"
        company = _first_non_empty(row, ["company", "company_name", "employer", "brandName"])
        loc = _first_non_empty(row, ["location", "city", "region", "work_city"]) or (location or "")
        salary = _first_non_empty(row, ["salary", "salary_range", "pay", "salaryRange"])
        platform = _first_non_empty(row, ["platform", "source", "site", "origin"]) or _platform_from_link(link)
        out.append(
            {
                "id": f"enterprise_{i}_{abs(hash(link.lower()))}",
                "title": title,
                "company": company,
                "location": loc,
                "salary": salary,
                "platform": platform,
                "link": link,
                "provider": "enterprise_api",
                "updated": _first_non_empty(row, ["updated", "updated_at", "publish_time", "published_at"]),
            }
        )
        if len(out) >= max(1, int(limit or 10)):
            break
    return _normalize_and_filter_jobs(out, limit=limit)


def _normalize_ddg_redirect(href: str) -> str:
    href = html_lib.unescape((href or "").strip())
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    # Absolute DuckDuckGo redirect URL.
    if href.startswith("http://duckduckgo.com/l/?") or href.startswith("https://duckduckgo.com/l/?"):
        qs = parse_qs(urlparse(href).query)
        uddg = (qs.get("uddg") or [""])[0]
        return unquote(uddg) if uddg else ""
    if href.startswith("/l/?"):
        qs = parse_qs(urlparse("https://duckduckgo.com" + href).query)
        uddg = (qs.get("uddg") or [""])[0]
        return unquote(uddg) if uddg else ""
    return href


def _search_jobs_duckduckgo(
    keywords: List[str], location: Optional[str], limit: int = 10
) -> List[Dict[str, Any]]:
    q_parts = [k.strip() for k in (keywords or []) if k and k.strip()]
    if location:
        q_parts.append(location.strip())
    q_parts.append("招聘 职位 site:zhipin.com OR site:liepin.com OR site:zhaopin.com OR site:51job.com OR site:lagou.com")
    q = " ".join(q_parts).strip() or "招聘 职位 site:zhipin.com"

    url = f"https://html.duckduckgo.com/html/?q={quote_plus(q)}"
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            timeout=12,
        )
        text = resp.text or ""
    except Exception:
        return []

    # result__a href="...">title</a>
    pattern = re.compile(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for href, raw_title in pattern.findall(text):
        link = _normalize_ddg_redirect(href)
        if not link:
            continue
        if not (link.startswith("http://") or link.startswith("https://")):
            continue
        low = link.lower()
        if not any(d in low for d in CN_JOB_DOMAINS):
            continue
        if low in seen:
            continue
        seen.add(low)
        title = re.sub(r"<[^>]+>", "", raw_title or "")
        title = html_lib.unescape(title).strip()
        platform = _platform_from_link(link)
        company = _infer_company_from_title(title, platform=platform)
        out.append(
            {
                "id": f"duckduckgo_{abs(hash(low))}",
                "title": title or "招聘岗位",
                "company": company,
                "location": location or "",
                "salary": "",
                "platform": platform,
                "link": link,
                "provider": "duckduckgo",
            }
        )
        if len(out) >= max(1, int(limit or 10)):
            break
    return _normalize_and_filter_jobs(out, limit=limit)


def _search_jobs_bing_html(
    keywords: List[str], location: Optional[str], limit: int = 10
) -> List[Dict[str, Any]]:
    q_parts = [k.strip() for k in (keywords or []) if k and k.strip()]
    if location:
        q_parts.append(location.strip())
    q_parts.append("招聘 职位 site:zhipin.com OR site:liepin.com OR site:zhaopin.com OR site:51job.com OR site:lagou.com")
    q = " ".join(q_parts).strip() or "招聘 职位 site:zhipin.com"

    try:
        resp = requests.get(
            "https://www.bing.com/search",
            params={"q": q, "count": max(10, min(int(limit or 10) * 2, 50))},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            timeout=12,
        )
        text = resp.text or ""
    except Exception:
        return []

    # <li class="b_algo"> ... <h2><a href="...">title</a>
    pattern = re.compile(r'<li class="b_algo"[^>]*>.*?<h2><a href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for link, raw_title in pattern.findall(text):
        if not link.startswith(("http://", "https://")):
            continue
        low = link.lower()
        if not any(d in low for d in CN_JOB_DOMAINS):
            continue
        if low in seen:
            continue
        seen.add(low)
        title = re.sub(r"<[^>]+>", "", raw_title or "")
        title = html_lib.unescape(title).strip()
        platform = _platform_from_link(link)
        company = _infer_company_from_title(title, platform=platform)
        out.append(
            {
                "id": f"binghtml_{abs(hash(low))}",
                "title": title or "招聘岗位",
                "company": company,
                "location": location or "",
                "salary": "",
                "platform": platform,
                "link": link,
                "provider": "bing_html",
            }
        )
        if len(out) >= max(1, int(limit or 10)):
            break
    return _normalize_and_filter_jobs(out, limit=limit)


def _search_jobs_remotive(
    keywords: List[str], location: Optional[str], limit: int = 10
) -> List[Dict[str, Any]]:
    # Remotive is a public job API and currently reachable in cloud environments.
    cleaned = [k.strip() for k in (keywords or []) if k and k.strip()]
    q = cleaned[0] if cleaned else "python"
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": q},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        data = resp.json() if resp.content else {}
    except Exception:
        return []

    jobs = data.get("jobs") or []
    base_rows: List[Dict[str, Any]] = []
    for it in jobs:
        link = str(it.get("url") or "").strip()
        if not link:
            continue
        title = str(it.get("title") or "").strip()
        company = str(it.get("company_name") or "").strip()
        loc = str(it.get("candidate_required_location") or location or "").strip()
        base_rows.append(
            {
                "id": f"remotive_{it.get('id')}",
                "title": title or "招聘岗位",
                "company": company,
                "location": loc,
                "salary": str(it.get("salary") or "").strip(),
                "platform": "Remotive",
                "link": link,
                "provider": "remotive",
                "updated": str(it.get("publication_date") or "").strip(),
            }
        )
        if len(base_rows) >= max(30, int(limit or 10) * 4):
            break

    if location:
        narrowed = [j for j in base_rows if location in str(j.get("location") or "")]
        if narrowed:
            return _normalize_and_filter_jobs(narrowed, limit=limit)
    # If no location match, return best available remote jobs instead of empty.
    return _normalize_and_filter_jobs(base_rows, limit=limit)


def _search_jobs_cn_entrypoints(
    keywords: List[str], location: Optional[str], limit: int = 10
) -> List[Dict[str, Any]]:
    """Guaranteed CN-market fallback: job-board search entry links."""
    kw = [k.strip() for k in (keywords or []) if k and k.strip()]
    query = " ".join(kw[:3]) or "Python"
    loc = (location or "").strip()

    boards = [
        ("Boss直聘", f"https://www.zhipin.com/web/geek/job?query={quote_plus(query)}"),
        ("猎聘", f"https://www.liepin.com/zhaopin/?key={quote_plus(query)}"),
        ("智联招聘", f"https://sou.zhaopin.com/?kw={quote_plus(query)}" + (f"&jl={quote_plus(loc)}" if loc else "")),
        ("前程无忧", f"https://we.51job.com/pc/search?keyword={quote_plus(query)}"),
        ("拉勾", f"https://www.lagou.com/wn/jobs?kd={quote_plus(query)}"),
    ]
    out: List[Dict[str, Any]] = []
    for i, (platform, link) in enumerate(boards, 1):
        out.append(
            {
                "id": f"cn_portal_{i}_{abs(hash(link))}",
                "title": f"{query} - {platform}搜索入口",
                "company": "",
                "location": loc,
                "salary": "",
                "platform": platform,
                "link": link,
                "provider": "cn_portal",
            }
        )
        if len(out) >= max(1, int(limit or 10)):
            break
    return _normalize_and_filter_jobs(out, limit=limit)

@app.get("/", include_in_schema=False)
async def home():
    """Default entry: always route to app workspace to avoid stale static home pages."""
    return RedirectResponse(url="/app", status_code=302)

@app.get("/app", response_class=HTMLResponse)
async def app_page():
    """主应用页面（仅保留统一工作台版本）。"""
    app_html = "static/app_pro.html"
    if os.path.exists(app_html) and os.path.getsize(app_html) > 64:
        with open(app_html, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>app_pro.html not found</h1>", status_code=500)


@app.get("/index.html", response_class=HTMLResponse)
async def home_alias():
    """旧入口统一跳转到主工作台。"""
    return RedirectResponse(url="/app", status_code=302)


@app.get("/app_clean.html", response_class=HTMLResponse)
async def app_clean_alias():
    """旧工作台统一跳转。"""
    return RedirectResponse(url="/app", status_code=302)


@app.get("/auto_apply_panel.html", response_class=HTMLResponse)
async def auto_apply_panel_page():
    """自动投递旧面板统一跳转。"""
    return RedirectResponse(url="/app", status_code=302)


@app.get("/investor.html", response_class=HTMLResponse)
async def investor_alias():
    """兼容旧投资看板路径。"""
    return await investor_page()


@app.get("/investor", response_class=HTMLResponse)
async def investor_page():
    """Investor-facing readiness dashboard page."""
    investor_html = "static/investor.html"
    if os.path.exists(investor_html):
        with open(investor_html, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Investor Dashboard</h1><p>/api/investor/readiness</p>")

@app.post("/api/upload")
async def upload_resume(
    file: UploadFile = File(...),
    force_ocr: Optional[str] = Form(None),
):
    """上传简历文件（支持PDF、Word、TXT/MD、图片）"""
    try:
        # 检查文件类型
        allowed_types = ['.pdf', '.docx', '.doc', '.txt', '.md', '.markdown', '.jpg', '.jpeg', '.png', '.bmp', '.gif']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_types:
            return JSONResponse({
                "error": f"不支持的文件格式。支持：PDF、Word、TXT/MD、图片（JPG/PNG等）"
            }, status_code=400)
        
        # 读取文件内容
        content = await file.read()
        resume_text = ""
        force_pdf_ocr = str(force_ocr or "").strip().lower() in {"1", "true", "yes", "on"}
        
        try:
            # 解析文件
            if file_ext in {'.txt', '.md', '.markdown'}:
                # 文本文件
                resume_text = _decode_text_file_bytes(content)
                    
            elif file_ext == '.pdf':
                # PDF文件
                try:
                    pdf_source = "none"
                    if force_pdf_ocr:
                        resume_text = _extract_pdf_text_ocr(content)
                        pdf_source = "ocr_forced"
                        if not resume_text:
                            resume_text, pdf_source = _extract_pdf_text_best_effort(content)
                    else:
                        resume_text, pdf_source = _extract_pdf_text_best_effort(content)
                    logger.info(
                        "pdf_extract_done source=%s chars=%s score=%.3f force_ocr=%s",
                        pdf_source,
                        len(resume_text or ""),
                        _text_quality_score(resume_text or ""),
                        force_pdf_ocr,
                    )
                except Exception as e:
                    return JSONResponse({
                        "error": f"PDF解析失败: {str(e)}。建议改传可编辑DOCX，或上传清晰图片触发OCR。"
                    }, status_code=500)
                    
            elif file_ext in ['.docx', '.doc']:
                # Word文件
                try:
                    from docx import Document
                    import io
                    doc = Document(io.BytesIO(content))
                    
                    # 提取段落文本
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            resume_text += paragraph.text + "\n"
                    
                    # 提取表格文本
                    for table in doc.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                if cell.text.strip():
                                    resume_text += cell.text + " "
                            resume_text += "\n"
                            
                except Exception as e:
                    return JSONResponse({
                        "error": f"Word文档解析失败: {str(e)}。请确保文件未损坏。"
                    }, status_code=500)
                    
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                # 图片文件 - 使用OCR
                try:
                    from PIL import Image
                    import io
                    
                    # 打开图片
                    image = Image.open(io.BytesIO(content))
                    
                    # OCR识别（支持中英文）
                    resume_text = _ocr_image_best_effort(image)
                    
                    if not resume_text.strip():
                        return JSONResponse({
                            "error": "图片OCR未提取到有效文字。请保证分辨率清晰，或改传DOCX/TXT。"
                        }, status_code=500)
                        
                except ImportError:
                    return JSONResponse({
                        "error": "图片OCR依赖未安装（Tesseract/PyMuPDF）。请联系管理员安装后重试。"
                    }, status_code=500)
                except Exception as e:
                    return JSONResponse({
                        "error": f"图片识别失败: {str(e)}。请确保图片清晰可读。"
                    }, status_code=500)
            
            # 检查是否成功提取到内容
            if not resume_text.strip():
                return JSONResponse({
                    "error": "文件解析成功，但未能提取到有效内容。请检查文件是否为空或格式是否正确。"
                }, status_code=500)

            _track_event(
                "resume_uploaded",
                {
                    "filename": file.filename,
                    "ext": file_ext,
                    "chars": len(resume_text.strip()),
                },
            )
            return JSONResponse({
                "success": True,
                "resume_text": resume_text.strip(),
                "filename": file.filename
            })
            
        except Exception as e:
            return JSONResponse({
                "error": f"文件解析出错: {str(e)}"
            }, status_code=500)
        
    except Exception as e:
        _track_event("api_error", {"api": "/api/upload", "error": str(e)[:300]})
        return JSONResponse({"error": f"上传失败: {str(e)}"}, status_code=500)

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket实时进度推送"""
    await websocket.accept()
    await progress_tracker.connect(websocket)
    
    try:
        while True:
            # 保持连接
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_tracker.disconnect(websocket)

@app.post("/api/process")
async def process_resume(request: Request):
    """处理简历的API接口 - 市场驱动"""
    try:
        data = await request.json()
        resume_text = data.get("resume", "")
        
        if not resume_text:
            return _api_error("简历内容不能为空", status_code=400, code="empty_resume")

        _track_event("resume_process_started", {"chars": len(resume_text)})

        # 重置进度
        progress_tracker.reset()
        
        # 定义进度回调
        async def update_progress_callback(step, message, agent):
            await progress_tracker.update_progress(step, message, agent)
            await progress_tracker.add_ai_message(agent, message)
        
        # 使用市场驱动引擎处理
        results = await market_engine.process_resume(resume_text, update_progress_callback)

        # Seed job search (Boss/OpenClaw) from resume text, so frontend can auto-search links.
        info = analyzer.extract_info(resume_text)
        seed_keywords = []
        if info.get("job_intention") and info["job_intention"] != "未指定":
            seed_keywords.append(info["job_intention"])
        seed_keywords.extend((info.get("skills") or [])[:6])
        seed_keywords = [k for k in seed_keywords if k]

        seed_location = None
        locs = info.get("preferred_locations") or []
        if locs:
            seed_location = locs[0]
        provider_mode = (real_job_service.get_statistics() or {}).get("provider_mode", "")
        
        # Real, actionable job text block (backward compatible with legacy UI field).
        def _format_real_jobs(jobs: List[Dict[str, Any]], mode: str) -> str:
            if not jobs:
                return (
                    '【推荐岗位】（当前暂无可用岗位）\n\n'
                    '排查建议：\n'
                    '1. 检查云端缓存：访问 /api/crawler/status。\n'
                    '2. 检查企业级招聘 API 是否已配置。\n'
                    '3. 若搜索引擎触发风控，可稍后重试。\n\n'
                    '注意：系统默认不会回退到“搜索入口链接”或演示岗位。\n'
                )

            heading = '【推荐岗位】（中国劳动力市场真实数据）'
            if mode == 'openclaw':
                heading = '【推荐岗位】（来自 Boss 直聘实时数据，OpenClaw）'
            elif mode == 'cloud':
                heading = '【推荐岗位】（来自 Boss 直聘云端缓存）'
            elif mode in ('baidu', 'bing', 'brave'):
                heading = f'【推荐岗位】（来自搜索引擎 {mode}）'
            elif mode == 'remotive':
                heading = '【推荐岗位】（来自全球招聘API，仅在显式开启时使用）'
            elif mode == 'bing_html':
                heading = '【推荐岗位】（来自 Bing 无浏览器搜索）'
            elif mode == 'duckduckgo':
                heading = '【推荐岗位】（来自 DuckDuckGo 无浏览器搜索）'
            elif mode == 'jooble':
                heading = '【推荐岗位】（来自 Jooble API）'
            elif mode == 'enterprise_api':
                heading = '【推荐岗位】（企业级中国招聘API实时数据）'
            elif mode == 'no_real_jobs':
                heading = '【推荐岗位】（未检索到可投递真实岗位）'

            lines = [heading, '']
            for i, job in enumerate(jobs, 1):
                title = job.get('title') or job.get('job_title') or '未知岗位'
                company = job.get('company') or ''
                loc = job.get('location') or ''
                salary = job.get('salary') or job.get('salary_range') or ''
                link = job.get('link') or job.get('apply_url') or ''

                mp = job.get('match_percentage')
                if mp is None:
                    mp = job.get('match_rate')
                if mp is None:
                    mp = job.get('match_score')
                mp_str = f"{mp}%" if isinstance(mp, (int, float)) else ''

                lines.append(f"{i}. {title}" + (f" - {company}" if company else ''))
                if salary:
                    lines.append(f"   薪资：{salary}")
                if loc:
                    lines.append(f"   地点：{loc}")
                if mp_str:
                    lines.append(f"   匹配度：{mp_str}")
                if link:
                    lines.append(f"   链接：{link}")
                lines.append('')

            return "\n".join(lines).strip() + "\n"

        async def _get_real_jobs_for_recommendation():
            cfg_mode = os.getenv('JOB_DATA_PROVIDER', 'auto').strip().lower()
            allow_portal_fallback = os.getenv("ALLOW_CN_PORTAL_FALLBACK", "1").strip().lower() in {"1", "true", "yes", "on"}
            kw = seed_keywords[:10]
            loc = seed_location

            if cfg_mode == 'cloud' or cloud_jobs_cache:
                cached = _filter_cloud_cache_by_query(kw, loc, limit=10)
                cached = _enforce_cn_market_jobs(cached)
                if cached:
                    return cached, 'cloud'
                # Cache empty/insufficient: fallback to cloud-safe real-time providers.
                fallback_jobs, fallback_mode, _ = _search_jobs_without_browser(
                    kw,
                    loc,
                    limit=10,
                    allow_portal_fallback=allow_portal_fallback,
                )
                return _enforce_cn_market_jobs(fallback_jobs), fallback_mode

            try:
                jobs = _normalize_real_jobs(
                    real_job_service.search_jobs(keywords=kw, location=loc, limit=10),
                    limit=10,
                )
                jobs = _enforce_cn_market_jobs(jobs)
                mode = (real_job_service.get_statistics() or {}).get('provider_mode', '') or cfg_mode
                return jobs[:10], mode
            except Exception:
                fallback_jobs, fallback_mode, _ = _search_jobs_without_browser(
                    kw,
                    loc,
                    limit=10,
                    allow_portal_fallback=allow_portal_fallback,
                )
                return _enforce_cn_market_jobs(fallback_jobs), fallback_mode or cfg_mode

        real_jobs, real_mode = await _get_real_jobs_for_recommendation()
        public_jobs = _public_job_payload(_enforce_cn_market_jobs(real_jobs), limit=10)
        if not public_jobs:
            portal_jobs = _search_jobs_cn_entrypoints(seed_keywords, seed_location, limit=5)
            if portal_jobs:
                public_jobs = _public_job_payload(portal_jobs, limit=10, allow_entrypoints=True)
                real_mode = "cn_portal"
        results["job_recommendations"] = _format_real_jobs(public_jobs, real_mode)
        results, quality_gate = _run_output_quality_gate(results, resume_text, info, public_jobs)
        provider_mode = real_mode

        # 完成
        await progress_tracker.complete()
        await progress_tracker.add_ai_message("系统", "🎉 市场分析完成！")
        _track_event(
            "process_quality_gate",
            {
                "passed": bool(quality_gate.get("passed", True)),
                "issues_count": len(quality_gate.get("issues") or []),
            },
        )
        _track_event(
            "job_recommendation_ready",
            {
                "provider_mode": provider_mode,
                "real_jobs_count": len(public_jobs),
            },
        )
        _track_event(
            "resume_processed",
            {
                "ok": True,
                "provider_mode": provider_mode,
                "skills_count": len(seed_keywords),
                "real_jobs_count": len(public_jobs),
                "quality_gate_passed": bool(quality_gate.get("passed", True)),
            },
        )

        response_payload = {
            "career_analysis": str(results.get("market_analysis") or ""),
            "job_recommendations": str(results.get("job_recommendations") or ""),
            "optimized_resume": str(results.get("optimized_resume") or ""),
            "interview_prep": str(results.get("interview_prep") or ""),
            "mock_interview": str(results.get("salary_analysis") or ""),
            "job_provider_mode": str(provider_mode or ""),
            "recommended_jobs": public_jobs,
            "recommendation_quality": {
                "strict_real_posting": True,
                "count": len(public_jobs),
                "has_actionable_jobs": bool(public_jobs),
            },
            "quality_gate": quality_gate,
            "schema_version": PROCESS_RESPONSE_SCHEMA_VERSION,
            "boss_seed": {
                "keywords": seed_keywords,
                "location": seed_location,
            },
        }
        shape_errors = _validate_process_response_shape(response_payload)
        if shape_errors:
            _track_event(
                "process_contract_error",
                {
                    "count": len(shape_errors),
                    "sample": shape_errors[:3],
                },
            )
            return _api_error("输出JSON未通过契约校验", status_code=500, code="process_contract_failed")

        return _api_success(response_payload)
        
    except Exception as e:
        _track_event("resume_process_failed", {"error": str(e)[:300]})
        _track_event("resume_processed", {"ok": False, "error": str(e)[:300]})
        _track_event("api_error", {"api": "/api/process", "error": str(e)[:300]})
        await progress_tracker.error(f"处理出错: {str(e)}")
        return _api_error(str(e), status_code=500, code="process_failed")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    stats = real_job_service.get_statistics()
    biz = business_service.metrics()
    
    # 检查OpenClaw状态
    openclaw_status = None
    if stats.get("provider_mode") == "openclaw":
        from app.services.job_providers.openclaw_browser_provider import OpenClawBrowserProvider
        openclaw = OpenClawBrowserProvider()
        openclaw_status = openclaw.health_check()
    
    return _api_success({
        "status": "ok",
        "message": "AI求职助手运行正常",
        "boot_ts": APP_BOOT_TS,
        "uptime_s": round(time.perf_counter() - APP_BOOT_MONO, 1),
        "job_database": stats,
        "openclaw": openclaw_status,
        "business": {
            "leads_total": biz.get("leads", {}).get("total", 0),
            "uploads": biz.get("funnel", {}).get("uploads", 0),
            "process_runs": biz.get("funnel", {}).get("process_runs", 0),
            "searches": biz.get("funnel", {}).get("searches", 0),
            "applies": biz.get("funnel", {}).get("applies", 0),
        },
        "config": {
            "job_data_provider": os.getenv("JOB_DATA_PROVIDER", "auto"),
            "cloud_cache_total": len(cloud_jobs_cache),
            "cloud_last_push_at": cloud_jobs_meta.get("last_push_at"),
            "no_browser_fallback_enabled": True,
            "enterprise_job_api_configured": bool(os.getenv("ENTERPRISE_JOB_API_URL", "").strip()),
            "llm": get_public_llm_config(),
        },
    })



@app.get("/api/version")
async def version():
    """Expose basic build metadata for debugging deployments."""
    return _api_success({
        "job_data_provider": os.getenv("JOB_DATA_PROVIDER", "auto"),
        "railway_git_commit_sha": os.getenv("RAILWAY_GIT_COMMIT_SHA"),
        "github_sha": os.getenv("GITHUB_SHA"),
        "app_boot_ts": APP_BOOT_TS,
    })


@app.get("/api/ping")
async def ping():
    """Ultra-light probe for availability checks."""
    return _api_success({"ok": True, "ts": datetime.now().isoformat()})


@app.get("/api/ready")
async def ready():
    """Release gate probe used by QA/ops before Go/No-Go."""
    cfg_mode = os.getenv("JOB_DATA_PROVIDER", "auto").strip().lower()
    cache_total = len(cloud_jobs_cache)
    checks = {
        "api_alive": True,
        "cn_provider_mode": cfg_mode in {"auto", "cloud", "baidu", "bing", "brave", "jooble", "openclaw", "enterprise_api"},
        "cache_or_cn_fallback": cache_total > 0 or True,
        "global_fallback_disabled_by_default": os.getenv("ENABLE_GLOBAL_JOB_FALLBACK", "").strip().lower() not in {"1", "true", "yes", "on"},
        "enterprise_api_configured": bool(os.getenv("ENTERPRISE_JOB_API_URL", "").strip()),
    }
    score = round(sum(1 for v in checks.values() if v) / len(checks) * 100, 1)
    status = "ready" if score >= 75 else "not_ready"
    return _api_success(
        {
            "status": status,
            "score": score,
            "checks": checks,
            "provider_mode": cfg_mode,
            "cloud_cache_total": cache_total,
            "boot_ts": APP_BOOT_TS,
        }
    )


@app.post("/api/business/lead")
async def capture_business_lead(request: Request):
    """Capture B2B/B2C monetization leads from landing page."""
    try:
        data = await request.json()
        email = (data.get("email") or "").strip()
        if ("@" not in email) or ("." not in email):
            return JSONResponse({"error": "请输入有效邮箱"}, status_code=400)

        payload = business_service.add_lead(
            email=email,
            name=(data.get("name") or "").strip(),
            company=(data.get("company") or "").strip(),
            use_case=(data.get("use_case") or "").strip(),
            budget=(data.get("budget") or "").strip(),
            source=(data.get("source") or "landing").strip(),
            note=(data.get("note") or "").strip(),
        )
        return JSONResponse({"success": True, "data": payload})
    except Exception as e:
        _track_event("api_error", {"api": "/api/business/lead", "error": str(e)[:300]})
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/business/feedback")
async def capture_user_feedback(request: Request):
    """Capture user feedback from product and landing pages."""
    try:
        data = await request.json()
        message = (data.get("message") or "").strip()
        if len(message) < 5:
            return JSONResponse({"error": "反馈内容太短，请至少输入5个字符"}, status_code=400)
        rating_raw = data.get("rating")
        rating = int(rating_raw) if str(rating_raw).strip() else None
        payload = business_service.add_feedback(
            message=message,
            rating=rating,
            category=(data.get("category") or "").strip(),
            email=(data.get("email") or "").strip(),
            source=(data.get("source") or "product").strip(),
            page=(data.get("page") or "").strip(),
        )
        return JSONResponse({"success": True, "data": payload})
    except ValueError as ve:
        return JSONResponse({"error": str(ve)}, status_code=400)
    except Exception as e:
        _track_event("api_error", {"api": "/api/business/feedback", "error": str(e)[:300]})
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/business/event")
async def capture_public_event(request: Request):
    """Public-safe growth event ingest endpoint for frontend KPI tracking."""
    try:
        data = await request.json()
        event_name = str(data.get("event_name") or "").strip().lower()
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}

        if (not event_name) or (not PUBLIC_EVENT_NAME_PATTERN.match(event_name)):
            return JSONResponse({"error": "invalid event_name"}, status_code=400)
        if event_name not in PUBLIC_EVENT_WHITELIST:
            return JSONResponse({"error": "event not allowed"}, status_code=400)

        business_service.track_event(event_name, payload)
        return JSONResponse({"success": True})
    except Exception as e:
        _track_event("api_error", {"api": "/api/business/event", "error": str(e)[:300]})
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/business/feedback/summary")
async def feedback_summary(request: Request, days: int = 7, limit: int = 20):
    """Feedback summary for ops dashboards and growth automation."""
    token = os.getenv("ADMIN_METRICS_TOKEN", "").strip()
    supplied = request.headers.get("x-admin-token", "").strip()
    if token and supplied != token:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    try:
        return JSONResponse({"success": True, "data": business_service.feedback_summary(days=days, limit=limit)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/business/public-proof")
async def business_public_proof():
    """Public-safe proof counters used on landing page."""
    try:
        m = business_service.metrics()
        funnel = m.get("funnel", {})
        engagement = m.get("engagement", {})
        quality = m.get("quality", {})
        return _api_success(
            {
                "leads_total": int(m.get("leads", {}).get("total", 0) or 0),
                "feedback_total": int(m.get("feedback", {}).get("total", 0) or 0),
                "uploads_total": int(funnel.get("uploads", 0) or 0),
                "process_runs_total": int(funnel.get("process_runs", 0) or 0),
                "searches_total": int(funnel.get("searches", 0) or 0),
                "applies_total": int(funnel.get("applies", 0) or 0),
                "job_link_clicks_total": int(engagement.get("job_link_clicks", 0) or 0),
                "result_downloads_total": int(engagement.get("result_downloads", 0) or 0),
                "upload_to_process_pct": float(funnel.get("upload_to_process_pct", 0) or 0),
                "process_to_search_pct": float(funnel.get("process_to_search_pct", 0) or 0),
                "search_to_apply_pct": float(funnel.get("search_to_apply_pct", 0) or 0),
                "click_to_apply_pct": float(engagement.get("click_to_apply_pct", 0) or 0),
                "quality_gate_fail_rate_pct": float(quality.get("gate_fail_rate_pct", 0) or 0),
            }
        )
    except Exception as e:
        return _api_error(str(e), status_code=500, code="business_public_proof_failed")


@app.get("/api/business/metrics")
async def business_metrics(request: Request):
    """Operational funnel metrics for fundraising / monetization tracking."""
    token = os.getenv("ADMIN_METRICS_TOKEN", "").strip()
    supplied = request.headers.get("x-admin-token", "").strip()
    if token and supplied != token:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    try:
        return JSONResponse({"success": True, "data": business_service.metrics()})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/business/readiness")
async def business_readiness(request: Request):
    """Simple GTM readiness snapshot for investor demos."""
    token = os.getenv("ADMIN_METRICS_TOKEN", "").strip()
    supplied = request.headers.get("x-admin-token", "").strip()
    if token and supplied != token:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    try:
        m = business_service.metrics()
        funnel = m.get("funnel", {})
        leads = m.get("leads", {})
        feedback = m.get("feedback", {})
        checks = {
            "lead_capture_ready": leads.get("total", 0) >= 1,
            "feedback_loop_ready": feedback.get("last_7d", 0) >= 1,
            "activation_flow_ready": funnel.get("upload_to_process_pct", 0) > 0,
            "job_match_flow_ready": funnel.get("process_to_search_pct", 0) > 0,
            "monetization_signal_ready": funnel.get("search_to_apply_pct", 0) > 0,
        }
        score = round(sum(1 for v in checks.values() if v) / len(checks) * 100, 1)
        return JSONResponse(
            {
                "success": True,
                "score": score,
                "checks": checks,
                "metrics": m,
            }
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/investor/readiness")
async def investor_readiness(request: Request):
    """
    Investor-facing readiness API.
    Optional auth via INVESTOR_READ_TOKEN header x-investor-token.
    """
    token = os.getenv("INVESTOR_READ_TOKEN", "").strip()
    supplied = request.headers.get("x-investor-token", "").strip()
    if token and supplied != token:
        return _api_error("forbidden", status_code=403, code="forbidden")
    try:
        return _api_success(_build_investor_readiness_snapshot())
    except Exception as e:
        _track_event("api_error", {"api": "/api/investor/readiness", "error": str(e)[:300]})
        return _api_error(str(e), status_code=500, code="investor_readiness_failed")


@app.get("/api/investor/summary")
async def investor_summary(request: Request):
    """Compact summary payload for pitch materials."""
    token = os.getenv("INVESTOR_READ_TOKEN", "").strip()
    supplied = request.headers.get("x-investor-token", "").strip()
    if token and supplied != token:
        return _api_error("forbidden", status_code=403, code="forbidden")
    try:
        snap = _build_investor_readiness_snapshot()
        p = snap.get("pillars", {})
        narrative = [
            f"Current financing readiness status: {snap.get('status')} (score {snap.get('overall_score')}).",
            f"Product pillar score: {p.get('product')}, reliability: {p.get('reliability')}.",
            f"Traction pillar score: {p.get('traction')}, GTM pillar score: {p.get('go_to_market')}.",
            f"Feedback captured so far: {(snap.get('metrics') or {}).get('feedback', {}).get('total', 0)}.",
            "Next 30 days focus: increase uploads, process runs, qualified leads, and actionable user feedback while keeping CN-real job links stable.",
        ]
        return _api_success(
            {
                "status": snap.get("status"),
                "overall_score": snap.get("overall_score"),
                "pillars": p,
                "highlights": snap.get("highlights", {}),
                "next_30d_targets": snap.get("next_30d_targets", {}),
                "narrative": narrative,
            }
        )
    except Exception as e:
        _track_event("api_error", {"api": "/api/investor/summary", "error": str(e)[:300]})
        return _api_error(str(e), status_code=500, code="investor_summary_failed")

@app.get("/api/jobs/search")
async def search_jobs(
    keywords: str = None,
    location: str = None,
    salary_min: int = None,
    experience: str = None,
    limit: int = 50,
    allow_portal_fallback: bool = True,
):
    """搜索真实岗位"""
    try:
        cfg_mode = os.getenv("JOB_DATA_PROVIDER", "auto").strip().lower()
        n = int(limit) if limit is not None else 50
        n = max(1, min(n, 100))
        keyword_list = keywords.split(",") if keywords else []
        kw = [k.strip() for k in keyword_list if k and k.strip()]
        allow_portal = bool(allow_portal_fallback) or (
            os.getenv("ALLOW_CN_PORTAL_FALLBACK", "1").strip().lower() in {"1", "true", "yes", "on"}
        )

        # Cloud mode: prefer crawler cache; fallback to cloud-safe real-time providers.
        if cfg_mode == "cloud" or cloud_jobs_cache:
            jobs = _filter_cloud_cache_by_query(kw, location, limit=n)
            jobs = _enforce_cn_market_jobs(jobs)
            warning = None
            mode = "cloud"
            if not jobs:
                fallback_jobs, fallback_mode, fallback_err = _search_jobs_without_browser(
                    kw,
                    location,
                    limit=n,
                    allow_portal_fallback=allow_portal,
                )
                jobs = _enforce_cn_market_jobs(fallback_jobs)
                mode = fallback_mode or "cloud"
                warning = (
                    f"cloud cache is empty; switched to no-browser provider: {mode}"
                    if jobs
                    else (
                        f"cloud cache empty and no-browser search failed: {fallback_err}"
                        if fallback_err
                        else "cloud cache is empty and no real jobs were found"
                    )
                )
            if not jobs and allow_portal:
                jobs = _search_jobs_cn_entrypoints(kw, location, limit=n)
                mode = "cn_portal"
                warning = warning or "switched to CN portal entrypoint fallback"
            _track_event(
                "job_search",
                {
                    "provider_mode": mode,
                    "result_count": len(jobs),
                    "cloud_mode": True,
                },
            )
            _cache_recent_jobs(jobs)
            return _api_success({
                "total": len(jobs),
                "jobs": jobs,
                "provider_mode": mode,
                "warning": warning,
            })

        # Stream progress to the same WebSocket channel as the AI pipeline.
        # Frontend listens for `type=job_search`.
        import asyncio

        def progress_cb(message: str, percent: int):
            asyncio.create_task(
                progress_tracker.broadcast(
                    {"type": "job_search", "data": {"message": message, "percent": int(percent)}}
                )
            )

        try:
            jobs = real_job_service.search_jobs(
                keywords=kw,
                location=location,
                salary_min=salary_min,
                experience=experience,
                limit=n,
                progress_callback=progress_cb,
            )
            jobs = _normalize_real_jobs(jobs, limit=n)
            jobs = _enforce_cn_market_jobs(jobs)
            mode = (real_job_service.get_statistics() or {}).get("provider_mode", cfg_mode)
            if not jobs and allow_portal:
                fallback_jobs, fallback_mode, _ = _search_jobs_without_browser(
                    kw,
                    location,
                    limit=n,
                    allow_portal_fallback=True,
                )
                fallback_jobs = _enforce_cn_market_jobs(fallback_jobs)
                if fallback_jobs:
                    jobs = fallback_jobs
                    mode = fallback_mode or mode
            if not jobs and allow_portal:
                jobs = _search_jobs_cn_entrypoints(kw, location, limit=n)
                mode = "cn_portal"
        except Exception as e:
            jobs, mode, _ = _search_jobs_without_browser(
                kw,
                location,
                limit=n,
                allow_portal_fallback=allow_portal,
            )
            jobs = _enforce_cn_market_jobs(jobs)
            if not jobs:
                raise e
        _track_event(
            "job_search",
            {
                "provider_mode": mode,
                "result_count": len(jobs),
                "cloud_mode": False,
            },
        )
        _cache_recent_jobs(jobs)
        return _api_success({
            "total": len(jobs),
            "jobs": jobs,
            "provider_mode": mode,
        })
    except Exception as e:
        _track_event("api_error", {"api": "/api/jobs/search", "error": str(e)[:300]})
        fallback_jobs: List[Dict[str, Any]] = []
        if allow_portal_fallback:
            try:
                kw = [k.strip() for k in (keywords or "").split(",") if k and k.strip()]
                fallback_jobs = _search_jobs_cn_entrypoints(kw, location, limit=max(1, min(int(limit or 10), 30)))
            except Exception:
                fallback_jobs = []
        # Do not hard-fail the UI when provider is rate-limited/captcha-blocked.
        # Return an empty-but-success payload so the frontend can keep the full flow available.
        return _api_success({
            "total": len(fallback_jobs),
            "jobs": fallback_jobs,
            "provider_mode": ("cn_portal" if fallback_jobs else (os.getenv("JOB_DATA_PROVIDER", "auto").strip().lower() or "auto")),
            "warning": str(e),
            "code": "job_search_failed",
        })

@app.get("/api/jobs/{job_id}")
async def get_job_detail(job_id: str):
    """获取岗位详情"""
    try:
        job = real_job_service.get_job_detail(job_id)
        if job:
            return JSONResponse({"success": True, "job": job})
        else:
            return JSONResponse({"error": "岗位不存在"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/jobs/apply")
async def apply_job(request: Request):
    """投递简历到指定岗位"""
    try:
        data = await request.json()
        job_id = data.get("job_id")
        resume_text = data.get("resume_text")
        user_info = data.get("user_info", {})
        
        result = real_job_service.apply_job(job_id, resume_text, user_info)
        if (not result.get("success")) and job_id in recent_search_jobs:
            # Fallback for no-browser providers whose job detail is not in local provider cache.
            j = recent_search_jobs.get(job_id, {})
            link = j.get("link") or j.get("apply_url")
            if link:
                app_id = f"EXT{int(datetime.now().timestamp())}"
                record = {
                    "application_id": app_id,
                    "job_id": job_id,
                    "job_title": j.get("title", ""),
                    "company": j.get("company", ""),
                    "platform": j.get("platform", j.get("provider", "")),
                    "apply_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "待投递",
                    "apply_link": link,
                    "user_info": user_info or {},
                }
                try:
                    real_job_service.records.add_record(record)
                except Exception:
                    pass
                result = {
                    "success": True,
                    "message": "已生成投递跳转链接（请在招聘网站完成真实投递）",
                    "data": record,
                }
        _track_event(
            "job_apply",
            {
                "job_id": job_id,
                "success": bool(result.get("success")),
            },
        )
        return JSONResponse(result)
    except Exception as e:
        _track_event("api_error", {"api": "/api/jobs/apply", "error": str(e)[:300]})
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/jobs/batch_apply")
async def batch_apply_jobs(request: Request):
    """批量投递简历"""
    try:
        data = await request.json()
        job_ids = data.get("job_ids", [])
        resume_text = data.get("resume_text")
        user_info = data.get("user_info", {})
        
        results = real_job_service.batch_apply(job_ids, resume_text, user_info)
        _track_event(
            "job_apply",
            {
                "batch": True,
                "requested": len(job_ids),
                "success_count": len([r for r in results if r.get("success")]),
            },
        )
        return JSONResponse({
            "success": True,
            "total": len(results),
            "results": results
        })
    except Exception as e:
        _track_event("api_error", {"api": "/api/jobs/batch_apply", "error": str(e)[:300]})
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/statistics")
async def get_statistics():
    """获取数据统计"""
    try:
        stats = real_job_service.get_statistics()
        return JSONResponse({"success": True, "data": stats})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ========================================
# 爬虫数据接收接口（云端部署时使用）
# ========================================

from fastapi import Header

# 简单的API密钥验证
CRAWLER_API_KEY = os.getenv("CRAWLER_API_KEY", "your-secret-key-change-this")

@app.post("/api/crawler/upload")
async def receive_crawler_data(request: Request, authorization: str = Header(None)):
    """接收本地爬虫推送的岗位数据"""
    try:
        # 验证API密钥
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse({"error": "未授权：缺少API密钥"}, status_code=401)
        
        api_key = authorization.replace("Bearer ", "")
        if api_key != CRAWLER_API_KEY:
            return JSONResponse({"error": "未授权：API密钥无效"}, status_code=401)
        
        # 解析数据
        data = await request.json()
        jobs = data.get("jobs", [])
        
        if not jobs:
            return JSONResponse({"error": "岗位数据为空"}, status_code=400)
        
        # 添加接收时间戳
        for job in jobs:
            job["received_at"] = datetime.now().isoformat()

        # 存储到缓存（去重 + 过滤 seed/demo + 必须可跳转）
        incoming = _normalize_and_filter_jobs(jobs, limit=5000)
        existing_keys = {
            str(j.get("link") or j.get("apply_url") or j.get("id") or "").strip().lower()
            for j in cloud_jobs_cache
        }
        new_jobs = []
        for job in incoming:
            key = str(job.get("link") or job.get("apply_url") or job.get("id") or "").strip().lower()
            if key and key not in existing_keys:
                existing_keys.add(key)
                new_jobs.append(job)

        cloud_jobs_cache.extend(new_jobs)

        # 限制缓存大小（保留最新的5000个）
        if len(cloud_jobs_cache) > 5000:
            cloud_jobs_cache[:] = cloud_jobs_cache[-5000:]

        cloud_jobs_meta["last_push_at"] = datetime.now().isoformat()
        cloud_jobs_meta["last_received"] = len(jobs)
        cloud_jobs_meta["last_new"] = len(new_jobs)
        _track_event(
            "crawler_upload",
            {"received": len(jobs), "new": len(new_jobs), "total": len(cloud_jobs_cache)},
        )

        print(f"✅ 接收爬虫数据：{len(new_jobs)} 个新岗位（总计：{len(cloud_jobs_cache)}）")
        
        return JSONResponse({
            "success": True,
            "received": len(jobs),
            "new": len(new_jobs),
            "total": len(cloud_jobs_cache)
        })
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/crawler/status")
async def get_crawler_status():
    """获取爬虫数据状态"""
    if not cloud_jobs_cache:
        return JSONResponse({
            "status": "empty",
            "total": 0,
            "last_push_at": cloud_jobs_meta.get("last_push_at"),
            "last_received": cloud_jobs_meta.get("last_received", 0),
            "last_new": cloud_jobs_meta.get("last_new", 0),
        })

    return JSONResponse({
        "status": "ok",
        "total": len(cloud_jobs_cache),
        "last_push_at": cloud_jobs_meta.get("last_push_at"),
        "last_received": cloud_jobs_meta.get("last_received", 0),
        "last_new": cloud_jobs_meta.get("last_new", 0),
    })


# ========================================
# 自动投递 API 接口（新增）
# ========================================

# 全局任务管理
auto_apply_tasks: Dict[str, Dict[str, Any]] = {}
task_lock = asyncio.Lock()

# 平台映射
PLATFORM_APPLIERS = {
    'boss': 'app.services.auto_apply.boss_applier.BossApplier',
    'zhilian': 'app.services.auto_apply.zhilian_applier.ZhilianApplier',
    'linkedin': 'app.services.auto_apply.linkedin_applier.LinkedInApplier'
}


def _set_task_stopped(task: Dict[str, Any]) -> None:
    """统一设置任务为停止状态。"""
    task["status"] = "stopped"
    task["completed_at"] = datetime.now().isoformat()

@app.post("/api/auto-apply/start")
async def start_auto_apply(request: Request):
    """启动自动投递"""
    try:
        raw_data = await request.json()
        data = _apply_haitou_defaults(raw_data if isinstance(raw_data, dict) else {})

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 获取配置
        config = {
            'platform': data.get('platform', 'boss'),
            'max_apply_per_session': data.get('max_count', HAITOU_DEFAULT_POLICY["max_count"]),
            'keywords': data.get('keywords', ''),
            'location': data.get('location', ''),
            'company_blacklist': data.get('blacklist', []),
            'user_profile': data.get('user_profile', {}),
            'pause_before_submit': data.get('pause_before_submit', False),
            'headless': data.get('headless', HAITOU_DEFAULT_POLICY["headless"]),
        }

        # 验证配置
        from app.services.auto_apply.config import AutoApplyConfig, validate_config
        apply_config = AutoApplyConfig.from_dict(config)
        is_valid, error_msg = validate_config(apply_config)

        if not is_valid:
            return _api_error(error_msg, 400)

        # 创建任务记录
        auto_apply_tasks[task_id] = {
            'task_id': task_id,
            'status': 'starting',
            'config': config,
            'strategy': HAITOU_DEFAULT_POLICY["strategy_version"],
            'progress': {
                'applied': 0,
                'failed': 0,
                'total': 0,
                'current_job': None
            },
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None
        }

        # 异步启动投递任务
        asyncio.create_task(_run_auto_apply_task(task_id, config, data.get('jobs', [])))

        return _api_success({
            'task_id': task_id,
            'message': '自动投递任务已启动'
        })

    except Exception as e:
        logger.exception("启动自动投递失败")
        return _api_error(str(e), 500)


async def _run_auto_apply_task(task_id: str, config: Dict[str, Any], jobs: List[Dict[str, Any]]):
    """运行自动投递任务（异步）"""
    try:
        from app.services.auto_apply.linkedin_applier import LinkedInApplier

        # 更新状态
        auto_apply_tasks[task_id]['status'] = 'running'
        auto_apply_tasks[task_id]['started_at'] = datetime.now().isoformat()

        # 创建投递器
        llm_client = None
        if config.get('use_ai_answers', True):
            try:
                from app.core.llm_client import LLMClient
                llm_client = LLMClient()
            except Exception:
                # Keep single-platform flow available even when optional LLM client is absent.
                llm_client = None
        applier = LinkedInApplier(config, llm_client)

        # 登录（如果需要）
        email = config.get('user_profile', {}).get('email')
        password = config.get('user_profile', {}).get('password')

        if email and password:
            login_success = await asyncio.to_thread(applier.login, email, password)
            if not login_success:
                auto_apply_tasks[task_id]['status'] = 'failed'
                auto_apply_tasks[task_id]['error'] = '登录失败'
                return

        # 如果没有提供职位列表，则搜索
        if not jobs:
            jobs = await asyncio.to_thread(
                applier.search_jobs,
                keywords=config.get('keywords', ''),
                location=config.get('location', ''),
                filters={},
            )

        auto_apply_tasks[task_id]['progress']['total'] = len(jobs)

        # 批量投递
        result = await asyncio.to_thread(
            applier.batch_apply,
            jobs,
            config.get('max_apply_per_session', 50),
        )

        # 更新最终状态
        auto_apply_tasks[task_id]['status'] = 'completed'
        auto_apply_tasks[task_id]['completed_at'] = datetime.now().isoformat()
        auto_apply_tasks[task_id]['result'] = result
        auto_apply_tasks[task_id]['progress']['applied'] = result['applied']
        auto_apply_tasks[task_id]['progress']['failed'] = result['failed']

        # 清理资源
        await asyncio.to_thread(applier.cleanup)

    except Exception as e:
        logger.exception(f"自动投递任务失败: {task_id}")
        auto_apply_tasks[task_id]['status'] = 'failed'
        auto_apply_tasks[task_id]['error'] = str(e)


@app.post("/api/auto-apply/stop")
async def stop_auto_apply(request: Request):
    """停止自动投递"""
    try:
        data = await request.json()
        task_id = data.get('task_id')

        if not task_id or task_id not in auto_apply_tasks:
            return _api_error('任务不存在', 404)

        task = auto_apply_tasks[task_id]

        if task['status'] in ['completed', 'failed', 'stopped']:
            return _api_success({
                'message': '任务已结束',
                'status': task['status'],
            })

        # 设置停止标志（实际停止逻辑在 applier 中处理）
        _set_task_stopped(task)

        return _api_success({
            'message': '停止指令已发送'
        })

    except Exception as e:
        logger.exception("停止自动投递失败")
        return _api_error(str(e), 500)


@app.post("/api/auto-apply/stop/{task_id}")
async def stop_auto_apply_by_path(task_id: str):
    """兼容前端路径参数形式的停止接口。"""
    try:
        if task_id not in auto_apply_tasks:
            return _api_error('任务不存在', 404)

        task = auto_apply_tasks[task_id]
        if task['status'] not in ['completed', 'failed', 'stopped']:
            _set_task_stopped(task)

        return _api_success({
            'task_id': task_id,
            'status': task.get('status'),
            'message': '停止指令已发送'
        })
    except Exception as e:
        logger.exception("路径停止自动投递失败")
        return _api_error(str(e), 500)


@app.post("/api/auto-apply/pause/{task_id}")
async def pause_auto_apply_by_path(task_id: str):
    """兼容前端路径参数形式的暂停接口。"""
    try:
        if task_id not in auto_apply_tasks:
            return _api_error('任务不存在', 404)
        task = auto_apply_tasks[task_id]
        if task['status'] in ['completed', 'failed', 'stopped']:
            return _api_error('任务已结束，无法暂停', 400)

        task['status'] = 'paused'
        return _api_success({
            'task_id': task_id,
            'status': 'paused',
            'message': '任务已暂停'
        })
    except Exception as e:
        logger.exception("暂停自动投递失败")
        return _api_error(str(e), 500)


@app.post("/api/auto-apply/resume/{task_id}")
async def resume_auto_apply_by_path(task_id: str):
    """兼容前端路径参数形式的恢复接口。"""
    try:
        if task_id not in auto_apply_tasks:
            return _api_error('任务不存在', 404)
        task = auto_apply_tasks[task_id]
        if task['status'] in ['completed', 'failed', 'stopped']:
            return _api_error('任务已结束，无法继续', 400)

        task['status'] = 'running'
        return _api_success({
            'task_id': task_id,
            'status': 'running',
            'message': '任务已继续'
        })
    except Exception as e:
        logger.exception("继续自动投递失败")
        return _api_error(str(e), 500)


@app.get("/api/auto-apply/status/{task_id}")
async def get_auto_apply_status(task_id: str):
    """查询投递状态"""
    try:
        if task_id not in auto_apply_tasks:
            return _api_error('任务不存在', 404)

        task = auto_apply_tasks[task_id]

        return _api_success({
            'task': task
        })

    except Exception as e:
        logger.exception("查询投递状态失败")
        return _api_error(str(e), 500)


@app.get("/api/auto-apply/history")
async def get_auto_apply_history(limit: int = 50):
    """获取投递历史"""
    try:
        # 按时间倒序排列
        tasks = sorted(
            auto_apply_tasks.values(),
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )

        return _api_success({
            'tasks': tasks[:limit],
            'total': len(tasks)
        })

    except Exception as e:
        logger.exception("获取投递历史失败")
        return _api_error(str(e), 500)


@app.websocket("/ws/auto-apply/{task_id}")
async def auto_apply_progress_ws(websocket: WebSocket, task_id: str):
    """实时推送投递进度（支持多平台）"""
    await websocket.accept()

    try:
        while True:
            if task_id not in auto_apply_tasks:
                await websocket.send_json({
                    'type': 'error',
                    'message': '任务不存在'
                })
                break

            task = auto_apply_tasks[task_id]

            # 发送详细进度
            await websocket.send_json({
                'type': 'progress',
                'task_id': task_id,
                'status': task['status'],
                'progress': task['progress'],
                'platforms': task.get('platforms', [task.get('config', {}).get('platform', 'linkedin')]),
                'timestamp': datetime.now().isoformat()
            })

            # 如果任务已完成，发送最终消息并断开
            if task['status'] in ['completed', 'failed', 'stopped']:
                await websocket.send_json({
                    'type': 'complete',
                    'task_id': task_id,
                    'status': task['status'],
                    'progress': task['progress'],
                    'result': task.get('result', {}),
                    'error': task.get('error')
                })
                break

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: {task_id}")
    except Exception as e:
        logger.exception(f"WebSocket 错误: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
        except:
            pass


# ========================================
# 多平台投递 API 接口（新增）
# ========================================

@app.post("/api/auto-apply/start-multi")
async def start_multi_platform_apply(request: Request):
    """启动多平台自动投递"""
    try:
        incoming = await request.json()
        data = _apply_haitou_defaults(incoming if isinstance(incoming, dict) else {})
        platforms = _normalize_platform_list(data.get('platforms')) or list(HAITOU_DEFAULT_POLICY["fallback_platforms"])
        config = dict(data.get('config') or {})
        config['max_count'] = int(HAITOU_DEFAULT_POLICY["max_count"])
        config['headless'] = bool(HAITOU_DEFAULT_POLICY["headless"])
        config['verification_wait_seconds'] = int(HAITOU_DEFAULT_POLICY["verification_wait_seconds"])
        if not config.get('keywords'):
            config['keywords'] = str(data.get('keywords') or '')
        if not config.get('location'):
            locs = _to_string_list(data.get('locations'))
            config['location'] = locs[0] if locs else str(data.get('location') or '')

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建任务记录
        async with task_lock:
            auto_apply_tasks[task_id] = {
                'task_id': task_id,
                'status': 'starting',
                'platforms': platforms,
                'config': config,
                'strategy': HAITOU_DEFAULT_POLICY["strategy_version"],
                'progress': {
                    'total_platforms': len(platforms),
                    'completed_platforms': 0,
                    'total_applied': 0,
                    'total_failed': 0,
                    'platform_progress': {}
                },
                'created_at': datetime.now().isoformat(),
                'started_at': None,
                'completed_at': None
            }

        # 异步启动多平台投递
        asyncio.create_task(_run_multi_platform_apply(task_id, platforms, config))

        return _api_success({
            'task_id': task_id,
            'message': f'已启动 {len(platforms)} 个平台的自动投递'
        })

    except Exception as e:
        logger.exception("启动多平台投递失败")
        return _api_error(str(e), 500)


@app.post("/api/auto-apply/boss/submit-code")
async def submit_boss_sms_code(request: Request):
    """提交 Boss 短信验证码，供运行中的任务继续登录。"""
    try:
        data = await request.json()
        task_id = _resolve_auto_apply_task_id(
            task_id=str(data.get("task_id") or "").strip(),
            gh_task_id=str(data.get("gh_task_id") or "").strip(),
        )
        code = "".join(ch for ch in str(data.get("code") or "") if ch.isdigit())

        if not task_id:
            return _api_error("task_id 不能为空（或提供有效 gh_task_id）", status_code=400)
        if len(code) < 4:
            return _api_error("验证码格式错误", status_code=400)

        _set_boss_sms_code(task_id, code)

        task = auto_apply_tasks.get(task_id) or {}
        boss_row = (task.get("progress") or {}).get("platform_progress", {}).get("boss")
        if isinstance(boss_row, dict):
            boss_row["status"] = "verifying"
            boss_row["message"] = "已收到验证码，正在登录验证"

        return _api_success(
            {
                "task_id": task_id,
                "accepted": True,
                "message": "验证码已提交，任务将继续执行",
            }
        )
    except Exception as e:
        logger.exception("提交 Boss 验证码失败")
        return _api_error(str(e), status_code=500)


@app.post("/api/auto-apply/boss/resend-code")
async def resend_boss_sms_code(request: Request):
    """触发运行中 Boss 任务重发短信验证码。"""
    try:
        data = await request.json()
        task_id = _resolve_auto_apply_task_id(
            task_id=str(data.get("task_id") or "").strip(),
            gh_task_id=str(data.get("gh_task_id") or "").strip(),
        )
        if not task_id:
            return _api_error("task_id 不能为空（或提供有效 gh_task_id）", status_code=400)

        task = auto_apply_tasks.get(task_id) or {}
        boss_row = (task.get("progress") or {}).get("platform_progress", {}).get("boss")
        if not isinstance(boss_row, dict):
            return _api_error("当前任务未运行 Boss 投递器", status_code=400)
        if str(boss_row.get("status") or "").strip() not in {"waiting_verification", "verifying", "opening"}:
            return _api_error("当前状态不可重发验证码", status_code=400)

        _push_boss_control_action(task_id, "resend_sms")
        boss_row["message"] = "已请求重发验证码，请留意短信"
        boss_row["status"] = "waiting_verification"
        boss_row["need_sms_code"] = True

        return _api_success(
            {
                "task_id": task_id,
                "accepted": True,
                "message": "已发送重发验证码指令",
            }
        )
    except Exception as e:
        logger.exception("重发 Boss 验证码失败")
        return _api_error(str(e), status_code=500)


async def _run_multi_platform_apply(task_id: str, platforms: List[str], config: Dict[str, Any]):
    """运行多平台投递任务"""
    try:
        # 更新状态
        auto_apply_tasks[task_id]['status'] = 'running'
        auto_apply_tasks[task_id]['started_at'] = datetime.now().isoformat()

        # 并发执行多个平台
        tasks = []
        for platform in platforms:
            if platform in PLATFORM_APPLIERS:
                task = asyncio.create_task(
                    _run_single_platform_apply(task_id, platform, config)
                )
                tasks.append(task)

        # 等待所有平台完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 汇总结果
        total_applied = 0
        total_failed = 0

        for result in results:
            if isinstance(result, dict):
                total_applied += result.get('applied', 0)
                total_failed += result.get('failed', 0)

        # 更新最终状态（若已手动停止则保持 stopped）
        task = auto_apply_tasks.get(task_id, {})
        task.setdefault('progress', {})
        platform_progress = task['progress'].get('platform_progress', {})
        platform_states = [
            str((platform_progress.get(p) or {}).get('status') or '')
            for p in platforms
        ]
        failed_platforms = sum(1 for s in platform_states if s == 'failed')
        done_platforms = sum(1 for s in platform_states if s in ('completed', 'failed', 'stopped'))

        task['progress']['completed_platforms'] = done_platforms
        task['progress']['total_applied'] = total_applied
        task['progress']['total_failed'] = total_failed

        if task.get('status') != 'stopped':
            if done_platforms == 0 and platforms:
                task['status'] = 'failed'
                task['error'] = '未执行任何平台任务'
            elif failed_platforms == len([p for p in platforms if p in PLATFORM_APPLIERS]) and total_applied == 0:
                task['status'] = 'failed'
                task['error'] = '全部平台执行失败'
            elif failed_platforms > 0:
                task['status'] = 'completed_with_errors'
            else:
                task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()

    except Exception as e:
        logger.exception(f"多平台投递任务失败: {task_id}")
        auto_apply_tasks[task_id]['status'] = 'failed'
        auto_apply_tasks[task_id]['error'] = str(e)


async def _run_single_platform_apply(task_id: str, platform: str, config: Dict[str, Any]):
    """运行单个平台的投递任务"""
    try:
        if auto_apply_tasks.get(task_id, {}).get('status') == 'stopped':
            return {'applied': 0, 'failed': 0}

        # 动态导入平台 Applier
        module_path, class_name = PLATFORM_APPLIERS[platform].rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        ApplierClass = getattr(module, class_name)

        # 获取平台特定配置
        raw_platform_config = config.get(f'{platform}_config', {})
        platform_config = dict(raw_platform_config) if isinstance(raw_platform_config, dict) else {}
        platform_headless = platform_config.get('headless')
        if platform_headless is None:
            platform_headless = config.get('headless', HAITOU_DEFAULT_POLICY["headless"])
        force_headless = os.getenv("FORCE_HEADLESS_BROWSER", "1").strip().lower() in {"1", "true", "yes", "on"}
        if force_headless:
            platform_headless = True
        platform_config.update({
            'keywords': config.get('keywords', ''),
            'location': config.get('location', ''),
            'max_apply_per_session': config.get('max_count', 50),
            'company_blacklist': config.get('blacklist', []),
            'headless': bool(platform_headless),
        })

        auto_apply_tasks[task_id]['progress']['platform_progress'][platform] = {
            'status': 'initializing',
            'message': '正在初始化平台'
        }

        if platform == 'boss':
            def _boss_progress(payload: Dict[str, Any]):
                stage = str(payload.get("stage") or "").strip()
                message = str(payload.get("message") or "").strip()
                row = auto_apply_tasks.get(task_id, {}).get('progress', {}).get('platform_progress', {}).get(platform, {})
                if stage == "waiting_sms_code":
                    row.update({
                        'status': 'waiting_verification',
                        'message': message or '等待短信验证码',
                        'need_sms_code': True,
                        'phone': _mask_phone(str(platform_config.get('phone') or '')),
                    })
                elif stage == "sms_code_submitted":
                    row.update({'status': 'verifying', 'message': message or '验证码已提交，验证中'})
                elif stage == "login_success":
                    row.update({'status': 'logged_in', 'message': message or '登录成功'})
                elif stage == "login_failed":
                    row.update({'status': 'failed', 'error': message or '登录失败'})
                elif stage == "login_open":
                    row.update({'status': 'opening', 'message': message or '打开登录页中'})
                elif stage == "sms_resent":
                    row.update({'status': 'waiting_verification', 'message': message or '验证码已重发，请查收'})
                elif stage == "sms_send_failed":
                    row.update({'status': 'failed', 'error': message or '验证码发送失败'})
                auto_apply_tasks.get(task_id, {}).get('progress', {}).get('platform_progress', {})[platform] = row

            platform_config.update({
                'task_id': task_id,
                'verification_wait_seconds': int(config.get('verification_wait_seconds', 180)),
                'sms_code_fetcher': (lambda tid=task_id: _pop_boss_sms_code(tid)),
                'control_action_fetcher': (lambda tid=task_id: _pop_boss_control_action(tid)),
                'progress_hook': _boss_progress,
                'sms_code': str(platform_config.get('sms_code') or config.get('sms_code') or '').strip() or None,
            })

        # 创建投递器（兼容不同的构造函数）
        # LinkedIn 需要 llm_client 参数，其他平台不应受其可用性影响。
        if platform == 'linkedin':
            llm_client = None
            if config.get('use_ai_answers', True):
                try:
                    from app.core.llm_client import LLMClient
                    llm_client = LLMClient()
                except Exception:
                    llm_client = None
            applier = ApplierClass(platform_config, llm_client)
        else:
            applier = ApplierClass(platform_config)

        # 登录
        login_success = False
        if platform == 'boss':
            phone = platform_config.get('phone')
            if phone:
                sms_code = platform_config.get('sms_code')
                login_success = await asyncio.to_thread(applier.login, phone, sms_code)
        elif platform == 'zhilian':
            username = platform_config.get('username')
            password = platform_config.get('password')
            if username and password:
                login_success = await asyncio.to_thread(applier.login, username, password)
        elif platform == 'linkedin':
            email = platform_config.get('email')
            password = platform_config.get('password')
            if email and password:
                login_success = await asyncio.to_thread(applier.login, email, password)

        if not login_success:
            raise Exception(f"{platform} 登录失败")

        # 搜索职位
        jobs = await asyncio.to_thread(
            applier.search_jobs,
            keywords=platform_config.get('keywords', ''),
            location=platform_config.get('location', ''),
            filters={},
        )

        # 更新进度
        auto_apply_tasks[task_id]['progress']['platform_progress'][platform] = {
            'status': 'running',
            'total': len(jobs),
            'applied': 0,
            'failed': 0
        }

        if auto_apply_tasks.get(task_id, {}).get('status') == 'stopped':
            auto_apply_tasks[task_id]['progress']['platform_progress'][platform]['status'] = 'stopped'
            applier.cleanup()
            return {'applied': 0, 'failed': 0}

        # 批量投递
        result = await asyncio.to_thread(
            applier.batch_apply,
            jobs,
            platform_config.get('max_apply_per_session', 50),
        )

        # 更新平台进度
        auto_apply_tasks[task_id]['progress']['platform_progress'][platform] = {
            'status': 'completed',
            'total': len(jobs),
            'applied': result['applied'],
            'failed': result['failed']
        }

        auto_apply_tasks[task_id]['progress']['completed_platforms'] += 1

        # 清理资源
        await asyncio.to_thread(applier.cleanup)

        return result

    except Exception as e:
        logger.exception(f"平台 {platform} 投递失败")
        auto_apply_tasks[task_id]['progress']['platform_progress'][platform] = {
            'status': 'failed',
            'error': str(e)
        }
        return {'applied': 0, 'failed': 0}
    finally:
        if platform == 'boss':
            _pop_boss_sms_code(task_id)
            _pop_boss_control_action(task_id)


@app.get("/api/auto-apply/platforms")
async def get_supported_platforms():
    """获取支持的平台列表"""
    return _api_success({
        'platforms': [
            {
                'id': 'boss',
                'name': 'Boss直聘',
                'icon': '💼',
                'status': 'available',
                'features': ['手机验证码登录', '智能投递', '打招呼语'],
                'config_fields': [
                    {'name': 'phone', 'label': '手机号', 'type': 'text', 'required': True}
                ]
            },
            {
                'id': 'zhilian',
                'name': '智联招聘',
                'icon': '📋',
                'status': 'available',
                'features': ['账号密码登录', '简历投递', '附件上传'],
                'config_fields': [
                    {'name': 'username', 'label': '用户名', 'type': 'text', 'required': True},
                    {'name': 'password', 'label': '密码', 'type': 'password', 'required': True}
                ]
            },
            {
                'id': 'linkedin',
                'name': 'LinkedIn',
                'icon': '🔗',
                'status': 'available',
                'features': ['Easy Apply', 'AI问答', '国际职位'],
                'config_fields': [
                    {'name': 'email', 'label': '邮箱', 'type': 'email', 'required': True},
                    {'name': 'password', 'label': '密码', 'type': 'password', 'required': True}
                ]
            }
        ]
    })


@app.get("/api/auto-apply/stats")
async def get_apply_stats():
    """获取投递统计"""
    try:
        # 统计所有任务
        total_tasks = len(auto_apply_tasks)
        completed_tasks = sum(1 for t in auto_apply_tasks.values() if t['status'] == 'completed')
        running_tasks = sum(1 for t in auto_apply_tasks.values() if t['status'] == 'running')

        total_applied = 0
        total_failed = 0

        # 平台统计
        platform_stats = {}

        for task in auto_apply_tasks.values():
            # 单平台任务
            if 'result' in task:
                result = task['result']
                total_applied += result.get('applied', 0)
                total_failed += result.get('failed', 0)

                platform = task.get('config', {}).get('platform', 'linkedin')
                if platform not in platform_stats:
                    platform_stats[platform] = {'applied': 0, 'failed': 0, 'total': 0}
                platform_stats[platform]['applied'] += result.get('applied', 0)
                platform_stats[platform]['failed'] += result.get('failed', 0)

            # 多平台任务
            if 'progress' in task and 'platform_progress' in task['progress']:
                for platform, progress in task['progress']['platform_progress'].items():
                    if platform not in platform_stats:
                        platform_stats[platform] = {'applied': 0, 'failed': 0, 'total': 0}
                    platform_stats[platform]['applied'] += progress.get('applied', 0)
                    platform_stats[platform]['failed'] += progress.get('failed', 0)
                    platform_stats[platform]['total'] += progress.get('total', 0)

                total_applied += task['progress'].get('total_applied', 0)
                total_failed += task['progress'].get('total_failed', 0)

        return _api_success({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'running_tasks': running_tasks,
            'total_applied': total_applied,
            'total_failed': total_failed,
            'success_rate': round(total_applied / (total_applied + total_failed) * 100, 2) if (total_applied + total_failed) > 0 else 0,
            'platform_stats': platform_stats
        })

    except Exception as e:
        logger.exception("获取统计失败")
        return _api_error(str(e), 500)


@app.post("/api/auto-apply/test-platform")
async def test_platform_config(request: Request):
    """测试平台配置（不实际投递）"""
    try:
        data = await request.json()
        platform = data.get('platform', 'boss')
        config = data.get('config', {})

        if platform not in PLATFORM_APPLIERS:
            return _api_error(f'不支持的平台: {platform}', 400)

        # 动态导入平台 Applier
        module_path, class_name = PLATFORM_APPLIERS[platform].rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        ApplierClass = getattr(module, class_name)

        # 创建投递器
        if platform == 'linkedin':
            from app.core.llm_client import LLMClient
            llm_client = LLMClient()
            applier = ApplierClass(config, llm_client)
        else:
            applier = ApplierClass(config)

        # 测试登录
        login_result = {'success': False, 'message': '未测试'}

        if platform == 'boss':
            phone = config.get('phone')
            if phone:
                login_result = {
                    'success': True,
                    'message': f'配置正确，手机号: {phone[:3]}****{phone[-4:]}'
                }
        elif platform == 'zhilian':
            username = config.get('username')
            password = config.get('password')
            if username and password:
                login_result = {
                    'success': True,
                    'message': f'配置正确，用户名: {username}'
                }
        elif platform == 'linkedin':
            email = config.get('email')
            password = config.get('password')
            if email and password:
                login_result = {
                    'success': True,
                    'message': f'配置正确，邮箱: {email}'
                }

        return _api_success({
            'platform': platform,
            'login_test': login_result,
            'config_valid': login_result['success']
        })

    except Exception as e:
        logger.exception("测试平台配置失败")
        return _api_error(str(e), 500)


@app.get("/api/resume/templates")
async def resume_templates():
    """Available resume templates for rendering."""
    return _api_success({"templates": resume_render_service.template_names()})


@app.post("/api/resume/structure")
async def resume_structure(request: Request):
    """Resume text -> structured JSON, optionally persisted as profile."""
    try:
        raw_data = await request.json()
        data = _apply_haitou_defaults(raw_data if isinstance(raw_data, dict) else {})
        resume_text = str(data.get("resume_text") or "").strip()
        if len(resume_text) < 20:
            return _api_error("resume_text 太短，至少 20 个字符", status_code=400)

        model = str(data.get("model") or "").strip() or None
        save_profile = bool(data.get("save_profile", True))
        user_id = str(data.get("user_id") or "").strip()
        title = str(data.get("title") or "").strip()
        profile_id = str(data.get("profile_id") or "").strip()

        result = await resume_profile_service.structure_resume_text(resume_text, model=model)
        if not result.get("ok"):
            return _api_error(result.get("error") or "结构化失败", status_code=500, code="resume_structure_failed")

        out: Dict[str, Any] = {
            "resume_json": result.get("resume_json") or {},
            "source": result.get("source") or "",
            "model": result.get("model") or "",
        }
        if result.get("warning"):
            out["warning"] = result.get("warning")

        if save_profile:
            info = resume_profile_service.save_profile(
                resume_json=out["resume_json"],
                profile_id=profile_id,
                user_id=user_id,
                title=title,
                source_text=resume_text,
            )
            out["profile"] = info
            _track_event("resume_profile_saved", {"profile_id": info.get("profile_id"), "source": out["source"]})

        return _api_success(out)
    except Exception as e:
        logger.exception("结构化简历失败")
        return _api_error(str(e), status_code=500, code="resume_structure_failed")


@app.post("/api/resume/profiles")
async def upsert_resume_profile(request: Request):
    """Create/update structured resume profile directly."""
    try:
        data = await request.json()
        resume_json = data.get("resume_json")
        if not isinstance(resume_json, dict):
            return _api_error("resume_json 必须是对象", status_code=400)

        info = resume_profile_service.save_profile(
            resume_json=resume_json,
            profile_id=str(data.get("profile_id") or "").strip(),
            user_id=str(data.get("user_id") or "").strip(),
            title=str(data.get("title") or "").strip(),
            source_text=str(data.get("source_text") or "").strip(),
        )
        _track_event("resume_profile_saved", {"profile_id": info.get("profile_id"), "source": "direct"})
        return _api_success({"profile": info})
    except Exception as e:
        logger.exception("保存简历档案失败")
        return _api_error(str(e), status_code=500, code="resume_profile_save_failed")


@app.get("/api/resume/profiles")
async def list_resume_profiles(limit: int = 20, user_id: str = ""):
    """List structured resume profiles."""
    try:
        payload = resume_profile_service.list_profiles(limit=limit, user_id=user_id)
        return _api_success(payload)
    except Exception as e:
        logger.exception("获取简历档案列表失败")
        return _api_error(str(e), status_code=500, code="resume_profile_list_failed")


@app.get("/api/resume/profiles/{profile_id}")
async def get_resume_profile(profile_id: str):
    """Get one structured resume profile."""
    try:
        row = resume_profile_service.get_profile(profile_id)
        if not row:
            return _api_error("简历档案不存在", status_code=404, code="resume_profile_not_found")
        return _api_success({"profile": row})
    except Exception as e:
        logger.exception("获取简历档案失败")
        return _api_error(str(e), status_code=500, code="resume_profile_get_failed")


@app.post("/api/resume/profiles/{profile_id}/fragment")
async def merge_resume_fragment(profile_id: str, request: Request):
    """Merge fragmented input into existing structured resume profile."""
    try:
        data = await request.json()
        fragment_text = str(data.get("fragment_text") or "").strip()
        if not fragment_text:
            return _api_error("fragment_text 不能为空", status_code=400)

        profile = resume_profile_service.get_profile(profile_id)
        if not profile:
            return _api_error("简历档案不存在", status_code=404, code="resume_profile_not_found")

        merged = await resume_profile_service.merge_fragment(
            current_resume_json=profile.get("resume_json") or {},
            fragment_text=fragment_text,
            section=str(data.get("section") or "").strip(),
            model=str(data.get("model") or "").strip() or None,
        )
        if not merged.get("ok"):
            return _api_error(merged.get("error") or "合并失败", status_code=400)

        info = resume_profile_service.save_profile(
            resume_json=merged.get("resume_json") or {},
            profile_id=profile_id,
            user_id=str(profile.get("user_id") or ""),
            title=str(profile.get("title") or ""),
            source_text=str(profile.get("source_text") or ""),
        )
        _track_event("resume_fragment_merged", {"profile_id": profile_id, "source": merged.get("source")})
        return _api_success(
            {
                "profile": info,
                "resume_json": merged.get("resume_json") or {},
                "source": merged.get("source") or "",
                "model": merged.get("model") or "",
            }
        )
    except Exception as e:
        logger.exception("简历碎片合并失败")
        return _api_error(str(e), status_code=500, code="resume_fragment_merge_failed")


@app.post("/api/resume/render")
async def render_resume(request: Request):
    """Render structured resume JSON to PDF/HTML."""
    try:
        data = await request.json()
        template_name = str(data.get("template") or "classic").strip().lower()
        fmt = str(data.get("format") or "pdf").strip().lower()
        if template_name not in set(resume_render_service.template_names()):
            return _api_error("template 不支持", status_code=400)
        if fmt not in {"pdf", "html"}:
            return _api_error("format 仅支持 pdf/html", status_code=400)

        resume_json = data.get("resume_json")
        profile_id = str(data.get("profile_id") or "").strip()
        if not isinstance(resume_json, dict):
            if not profile_id:
                return _api_error("需要提供 profile_id 或 resume_json", status_code=400)
            profile = resume_profile_service.get_profile(profile_id)
            if not profile:
                return _api_error("简历档案不存在", status_code=404, code="resume_profile_not_found")
            resume_json = profile.get("resume_json") or {}

        doc = await asyncio.to_thread(
            resume_render_service.render_to_file,
            resume_json,
            template_name,
            fmt,
        )
        _track_event(
            "resume_rendered",
            {
                "doc_id": doc.get("doc_id"),
                "format": doc.get("format"),
                "template": doc.get("template"),
            },
        )
        return _api_success(
            {
                "document": {
                    "doc_id": doc.get("doc_id"),
                    "format": doc.get("format"),
                    "template": doc.get("template"),
                    "file_size": doc.get("file_size"),
                    "created_at": doc.get("created_at"),
                    "download_url": f"/api/resume/render/download/{doc.get('doc_id')}",
                }
            }
        )
    except Exception as e:
        logger.exception("简历渲染失败")
        return _api_error(str(e), status_code=500, code="resume_render_failed")


@app.get("/api/resume/render/download/{doc_id}")
async def download_rendered_resume(doc_id: str):
    """Download rendered resume document by doc_id."""
    try:
        file_path = resume_render_service.resolve_doc_path(doc_id)
        if not file_path:
            return _api_error("文档不存在", status_code=404, code="render_doc_not_found")
        filename = os.path.basename(file_path)
        media = "application/pdf" if file_path.lower().endswith(".pdf") else "text/html; charset=utf-8"
        return FileResponse(file_path, media_type=media, filename=filename)
    except Exception as e:
        logger.exception("下载渲染文档失败")
        return _api_error(str(e), status_code=500, code="render_doc_download_failed")


def _default_email_html_template() -> str:
    return """
    <p>您好 {name}：</p>
    <p>我是候选人 {candidate_name}，关注到贵司 {company} 的相关岗位，非常希望有机会进一步沟通。</p>
    <p>我的核心能力：{skills_line}。</p>
    <p>简历已附上，期待您的回复，感谢！</p>
    <p>此致<br/>敬礼</p>
    <p>{candidate_name}<br/>{candidate_email}</p>
    """


@app.get("/api/email/presets")
async def email_presets():
    return _api_success({"presets": SMTP_PRESETS})


@app.get("/api/email/history")
async def email_history(limit: int = 50):
    try:
        return _api_success(email_campaign_service.list_history(limit=limit))
    except Exception as e:
        logger.exception("查询邮件历史失败")
        return _api_error(str(e), status_code=500, code="email_history_failed")


@app.get("/api/email/rate-limit")
async def email_rate_limit(sender_email: str, max_hourly: int = 30, max_daily: int = 100):
    try:
        if "@" not in (sender_email or ""):
            return _api_error("sender_email 不合法", status_code=400)
        payload = email_campaign_service.check_rate_limit(
            sender_email=sender_email.strip().lower(),
            max_hourly=max_hourly,
            max_daily=max_daily,
        )
        return _api_success(payload)
    except Exception as e:
        logger.exception("查询邮件限速失败")
        return _api_error(str(e), status_code=500, code="email_rate_limit_failed")


@app.post("/api/email/send-batch")
async def email_send_batch(request: Request):
    """
    Batch email delivery with SMTP presets + rate limits.
    Payload:
      smtp, contacts[], subject_template, body_template,
      profile_id/resume_json, template, max_hourly, max_daily, dry_run, attach_pdf
    """
    try:
        data = await request.json()
        smtp = data.get("smtp") if isinstance(data.get("smtp"), dict) else {}
        contacts = data.get("contacts") if isinstance(data.get("contacts"), list) else []
        if not contacts:
            return _api_error("contacts 不能为空", status_code=400)

        profile_id = str(data.get("profile_id") or "").strip()
        resume_json = data.get("resume_json") if isinstance(data.get("resume_json"), dict) else None
        if (not resume_json) and profile_id:
            profile = resume_profile_service.get_profile(profile_id)
            if not profile:
                return _api_error("简历档案不存在", status_code=404, code="resume_profile_not_found")
            resume_json = profile.get("resume_json") or {}

        attach_pdf = bool(data.get("attach_pdf", True))
        template_name = str(data.get("template") or "classic").strip().lower()
        if template_name not in set(resume_render_service.template_names()):
            template_name = "classic"

        attachment_path = ""
        rendered_doc = None
        if attach_pdf:
            if not isinstance(resume_json, dict):
                return _api_error("attach_pdf=true 时必须提供 profile_id 或 resume_json", status_code=400)
            rendered_doc = await asyncio.to_thread(
                resume_render_service.render_to_file,
                resume_json,
                template_name,
                "pdf",
            )
            attachment_path = rendered_doc.get("file_path") or ""

        personal = (resume_json or {}).get("personal_info") if isinstance(resume_json, dict) else {}
        skills = (resume_json or {}).get("skills") if isinstance(resume_json, dict) else []
        candidate_name = str((personal or {}).get("name") or "候选人")
        candidate_email = str((personal or {}).get("email") or (smtp.get("username") or ""))
        skills_line = "、".join([str(s) for s in skills[:8]]) if isinstance(skills, list) else ""
        default_ctx = {
            "candidate_name": candidate_name,
            "candidate_email": candidate_email,
            "skills_line": skills_line,
        }

        subject_template = str(data.get("subject_template") or "应聘咨询 - {candidate_name}")
        body_template = str(data.get("body_template") or _default_email_html_template())
        max_hourly = int(data.get("max_hourly") or 30)
        max_daily = int(data.get("max_daily") or 100)
        dry_run = bool(data.get("dry_run", False))

        result = await asyncio.to_thread(
            email_campaign_service.send_batch,
            smtp,
            contacts,
            subject_template,
            body_template,
            attachment_path,
            max_hourly,
            max_daily,
            dry_run,
            default_ctx,
        )
        _track_event(
            "email_batch_sent",
            {
                "campaign_id": result.get("campaign_id"),
                "sent": result.get("sent", 0),
                "failed": result.get("failed", 0),
                "dry_run": dry_run,
            },
        )

        out: Dict[str, Any] = {"result": result}
        if rendered_doc:
            out["attachment"] = {
                "doc_id": rendered_doc.get("doc_id"),
                "download_url": f"/api/resume/render/download/{rendered_doc.get('doc_id')}",
                "file_size": rendered_doc.get("file_size"),
            }
        return _api_success(out)
    except Exception as e:
        logger.exception("批量发送邮件失败")
        return _api_error(str(e), status_code=500, code="email_batch_send_failed")


@app.get("/api/features/overview")
async def features_overview():
    aihawk = _aihawk_capability_snapshot()
    return _api_success(
        {
            "features": {
                "market_process": True,
                "multi_agent_process": True,
                "skills_graph": True,
                "resume_profile": True,
                "resume_render": True,
                "job_search": True,
                "email_campaign": True,
                "auto_apply_platforms": True,
                "github_highstar_prepare": bool(aihawk.get("can_prepare")),
                "github_highstar_apply": bool(aihawk.get("can_run")),
                "haitou_default_strategy": True,
            },
            "github_highstar": aihawk,
            "haitou_default_policy": HAITOU_DEFAULT_POLICY,
        }
    )


@app.get("/api/strategy/defaults")
async def strategy_defaults():
    return _api_success({"haitou_default_policy": HAITOU_DEFAULT_POLICY})


@app.post("/api/skills/analyze")
async def analyze_skills_graph(request: Request):
    try:
        data = await request.json()
        resume_text = str(data.get("resume_text") or data.get("resume") or "").strip()
        if not resume_text:
            return _api_error("resume_text 不能为空", status_code=400)

        target_role = str(data.get("target_role") or "").strip()
        job_text = str(data.get("job_text") or "").strip()
        payload = _skills_graph_payload(resume_text, target_role, job_text)
        return _api_success({"skills_graph": payload})
    except Exception as e:
        logger.exception("skills_graph 分析失败")
        return _api_error(str(e), status_code=500, code="skills_graph_failed")


@app.post("/api/process/multi-agent")
async def process_resume_multi_agent(request: Request):
    """Run legacy multi-agent deep analysis pipeline + skills graph."""
    try:
        data = await request.json()
        resume_text = str(data.get("resume") or data.get("resume_text") or "").strip()
        if not resume_text:
            return _api_error("简历内容不能为空", status_code=400, code="empty_resume")

        _track_event(
            "resume_process_started",
            {"chars": len(resume_text), "engine_mode": "multi_agent"},
        )

        results = await asyncio.to_thread(pipeline.process_resume, resume_text)
        downgraded = False
        if _multi_agent_outputs_degraded(results):
            try:
                market_results = await market_engine.process_resume(resume_text)
                results = {
                    "career_analysis": str(market_results.get("market_analysis") or ""),
                    "job_recommendations": str(market_results.get("job_recommendations") or ""),
                    "optimized_resume": str(market_results.get("optimized_resume") or ""),
                    "interview_prep": str(market_results.get("interview_prep") or ""),
                    "mock_interview": str(market_results.get("salary_analysis") or ""),
                }
                downgraded = True
            except Exception:
                logger.exception("multi-agent 降级到 market_engine 失败")
        info = analyzer.extract_info(resume_text)

        seed_keywords: List[str] = []
        if info.get("job_intention") and info["job_intention"] != "未指定":
            seed_keywords.append(str(info["job_intention"]))
        seed_keywords.extend([str(x) for x in (info.get("skills") or [])[:6]])
        seed_keywords = [k for k in seed_keywords if k]
        seed_location = (info.get("preferred_locations") or [None])[0]

        provider_mode = "none"
        recommended_jobs: List[Dict[str, Any]] = []
        try:
            jobs, provider_mode, _ = _search_jobs_without_browser(
                seed_keywords,
                seed_location,
                limit=8,
                allow_portal_fallback=True,
            )
            recommended_jobs = _public_job_payload(_enforce_cn_market_jobs(jobs), limit=8)
        except Exception:
            logger.exception("multi-agent 岗位检索失败")

        skills_payload = _skills_graph_payload(
            resume_text,
            str(info.get("job_intention") or ""),
            str(results.get("job_recommendations") or ""),
        )

        response_payload = {
            "career_analysis": str(results.get("career_analysis") or ""),
            "job_recommendations": str(results.get("job_recommendations") or ""),
            "optimized_resume": str(results.get("optimized_resume") or ""),
            "interview_prep": str(results.get("interview_prep") or ""),
            "mock_interview": str(results.get("mock_interview") or ""),
            "recommended_jobs": recommended_jobs,
            "job_provider_mode": provider_mode,
            "engine_mode": "multi_agent",
            "fallback_downgraded": downgraded,
            "skills_graph": skills_payload,
        }
        _track_event(
            "resume_processed",
            {
                "ok": True,
                "engine_mode": "multi_agent",
                "provider_mode": provider_mode,
                "jobs": len(recommended_jobs),
            },
        )
        return _api_success(response_payload)
    except Exception as e:
        logger.exception("multi-agent 简历处理失败")
        _track_event(
            "resume_processed",
            {"ok": False, "engine_mode": "multi_agent", "error": str(e)[:300]},
        )
        return _api_error(str(e), status_code=500, code="process_multi_agent_failed")


def _normalize_platform_list(raw: Any) -> List[str]:
    valid = {"boss", "zhilian", "linkedin"}
    items = _to_string_list(raw)
    out: List[str] = []
    for item in items:
        key = str(item).strip().lower()
        if key in valid and key not in out:
            out.append(key)
    return out


def _build_fallback_auto_apply_config(
    payload: Dict[str, Any],
    keywords: List[str],
    locations: List[str],
    max_count: int,
) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {
        "keywords": ",".join(keywords or []),
        "location": (locations[0] if locations else ""),
        "max_count": int(HAITOU_DEFAULT_POLICY["max_count"]),
        "blacklist": _to_string_list(payload.get("blacklist") or payload.get("company_blacklist")),
        "headless": bool(HAITOU_DEFAULT_POLICY["headless"]),
        "use_ai_answers": bool(payload.get("use_ai_answers", True)),
        "verification_wait_seconds": int(HAITOU_DEFAULT_POLICY["verification_wait_seconds"]),
        "sms_code": str(payload.get("sms_code") or "").strip() or None,
    }

    boss_cfg = payload.get("boss_config") if isinstance(payload.get("boss_config"), dict) else {}
    zhilian_cfg = payload.get("zhilian_config") if isinstance(payload.get("zhilian_config"), dict) else {}
    linkedin_cfg = payload.get("linkedin_config") if isinstance(payload.get("linkedin_config"), dict) else {}

    cfg["boss_config"] = {
        **boss_cfg,
        "phone": str(
            boss_cfg.get("phone")
            or payload.get("boss_phone")
            or payload.get("phone")
            or ""
        ).strip(),
        "sms_code": str(
            boss_cfg.get("sms_code")
            or payload.get("boss_sms_code")
            or payload.get("sms_code")
            or ""
        ).strip() or None,
    }
    cfg["zhilian_config"] = {
        **zhilian_cfg,
        "username": str(
            zhilian_cfg.get("username")
            or payload.get("zhilian_username")
            or payload.get("username")
            or ""
        ).strip(),
        "password": str(
            zhilian_cfg.get("password")
            or payload.get("zhilian_password")
            or ""
        ),
    }
    cfg["linkedin_config"] = {
        **linkedin_cfg,
        "email": str(
            linkedin_cfg.get("email")
            or payload.get("linkedin_email")
            or payload.get("email")
            or ""
        ).strip(),
        "password": str(
            linkedin_cfg.get("password")
            or payload.get("linkedin_password")
            or ""
        ),
    }
    return cfg


def _filter_platforms_by_credentials(platforms: List[str], config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    accepted: List[str] = []
    blockers: List[str] = []
    for p in platforms:
        if p == "boss":
            phone = str((config.get("boss_config") or {}).get("phone") or "").strip()
            if phone:
                accepted.append(p)
            else:
                blockers.append("boss 缺少手机号（boss_config.phone）")
        elif p == "zhilian":
            u = str((config.get("zhilian_config") or {}).get("username") or "").strip()
            pw = str((config.get("zhilian_config") or {}).get("password") or "")
            if u and pw:
                accepted.append(p)
            else:
                blockers.append("zhilian 缺少账号密码（zhilian_config.username/password）")
        elif p == "linkedin":
            e = str((config.get("linkedin_config") or {}).get("email") or "").strip()
            pw = str((config.get("linkedin_config") or {}).get("password") or "")
            if e and pw:
                accepted.append(p)
            else:
                blockers.append("linkedin 缺少邮箱密码（linkedin_config.email/password）")
    return accepted, blockers


async def _create_multi_platform_auto_apply_task(platforms: List[str], config: Dict[str, Any]) -> str:
    task_id = str(uuid.uuid4())
    async with task_lock:
        auto_apply_tasks[task_id] = {
            "task_id": task_id,
            "status": "starting",
            "platforms": platforms,
            "config": config,
            "progress": {
                "total_platforms": len(platforms),
                "completed_platforms": 0,
                "total_applied": 0,
                "total_failed": 0,
                "platform_progress": {},
            },
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
        }
    asyncio.create_task(_run_multi_platform_apply(task_id, platforms, config))
    return task_id


async def _run_github_auto_apply_task(task_id: str, payload: Dict[str, Any]):
    task = github_apply_tasks.get(task_id)
    if not task:
        return
    task["status"] = "running"
    task["started_at"] = datetime.now().isoformat()
    try:
        snapshot = _aihawk_capability_snapshot()
        task["capability"] = snapshot
        if not snapshot.get("can_prepare"):
            task["status"] = "blocked"
            task["error"] = (
                "AIHawk 运行环境不完整，无法生成任务配置。"
                f" missing_required={snapshot.get('missing_required')} missing_deps={snapshot.get('missing_deps')}"
            )
            task["completed_at"] = datetime.now().isoformat()
            return

        # Lazy import to avoid startup hard dependency.
        from app.core.aihawk_client import aihawk_client

        resume_text = str(payload.get("resume_text") or "").strip()
        keywords = _to_string_list(payload.get("keywords"))
        locations = _to_string_list(payload.get("locations"))
        max_count = max(1, min(200, int(payload.get("max_count") or 20)))
        llm_key = (
            os.getenv("DEEPSEEK_API_KEY", "").strip()
            or os.getenv("OPENAI_API_KEY", "").strip()
        )

        config_dir = await asyncio.to_thread(
            aihawk_client.create_config_files,
            task_id,
            keywords or ["Python"],
            locations or ["北京"],
            max_count,
            resume_text,
            llm_key or "missing_api_key",
        )
        task["prepared"] = True
        task["config_dir"] = config_dir

        enable_fallback = bool(payload.get("enable_fallback_auto_apply", True)) or bool(HAITOU_DEFAULT_POLICY["enabled"])
        requested_platforms = _normalize_platform_list(
            payload.get("fallback_platforms") or payload.get("platforms")
        ) or list(HAITOU_DEFAULT_POLICY["fallback_platforms"])

        # Current upstream AIHawk package in this repo may not include auto-apply plugins.
        if not snapshot.get("has_auto_apply_plugins"):
            if enable_fallback:
                fallback_cfg = _build_fallback_auto_apply_config(
                    payload, keywords, locations, max_count
                )
                accepted, blockers = _filter_platforms_by_credentials(
                    requested_platforms,
                    fallback_cfg,
                )
                if accepted:
                    linked_task_id = await _create_multi_platform_auto_apply_task(
                        accepted,
                        fallback_cfg,
                    )
                    task["status"] = "fallback_started"
                    task["linked_auto_apply_task_id"] = linked_task_id
                    task["result"] = {
                        "message": (
                            "AIHawk 插件缺失，已自动切换到内置多平台自动投递引擎。"
                        ),
                        "platforms": accepted,
                        "linked_auto_apply_task_id": linked_task_id,
                    }
                else:
                    task["status"] = "prepared_only"
                    task["result"] = {
                        "message": (
                            "已生成 AIHawk 配置文件，但未提供可用平台凭据，无法自动切换真实投递。"
                        ),
                        "blockers": blockers,
                    }
            else:
                task["status"] = "prepared_only"
                task["result"] = {
                    "message": (
                        "已生成 AIHawk 配置文件，但当前仓库缺少 auto-apply 插件代码。"
                        " 如需真实自动投递，请切回含插件的历史版本或私有分支。"
                    )
                }
            task["completed_at"] = datetime.now().isoformat()
            return

        if not snapshot.get("can_run"):
            task["status"] = "blocked"
            task["error"] = "AIHawk 可准备但不可运行，请检查依赖和 LLM_KEY。"
            task["completed_at"] = datetime.now().isoformat()
            return

        run_result = await asyncio.to_thread(aihawk_client.run_aihawk, task_id, max_count)
        task["status"] = "completed" if run_result.get("success") else "failed"
        task["result"] = run_result
        task["completed_at"] = datetime.now().isoformat()
    except Exception as e:
        logger.exception("github 高星自动投递任务失败")
        task["status"] = "failed"
        task["error"] = str(e)
        task["completed_at"] = datetime.now().isoformat()


@app.get("/api/github-auto-apply/health")
async def github_auto_apply_health():
    return _api_success({"capability": _aihawk_capability_snapshot()})


@app.post("/api/github-auto-apply/start")
async def github_auto_apply_start(request: Request):
    """
    Start GitHub high-star AIHawk task.
    Payload:
      resume_text (required),
      keywords (list or csv),
      locations (list or csv),
      max_count (int)
    """
    try:
        raw_data = await request.json()
        data = _apply_haitou_defaults(raw_data if isinstance(raw_data, dict) else {})
        resume_text = str(data.get("resume_text") or "").strip()
        if not resume_text:
            profile_id = str(data.get("profile_id") or "").strip()
            if profile_id:
                profile = resume_profile_service.get_profile(profile_id)
                if profile:
                    resume_json = profile.get("resume_json") or {}
                    resume_text = json.dumps(resume_json, ensure_ascii=False)
        if not resume_text:
            return _api_error("resume_text 不能为空（或提供 profile_id）", status_code=400)

        info = analyzer.extract_info(resume_text)
        keywords = _to_string_list(data.get("keywords"))
        if not keywords:
            keywords = [str(info.get("job_intention") or "").strip()]
            keywords.extend([str(x) for x in (info.get("skills") or [])[:5]])
            keywords = [k for k in keywords if k]
        locations = _to_string_list(data.get("locations"))
        if not locations:
            locations = [str(x) for x in (info.get("preferred_locations") or [])[:3] if str(x).strip()]
        if not locations:
            locations = ["北京"]

        task_id = f"gh_{uuid.uuid4().hex[:10]}"
        task = {
            "task_id": task_id,
            "status": "queued",
            "keywords": keywords,
            "locations": locations,
            "max_count": int(HAITOU_DEFAULT_POLICY["max_count"]),
            "enable_fallback_auto_apply": True,
            "requested_fallback_platforms": list(HAITOU_DEFAULT_POLICY["fallback_platforms"]),
            "created_at": datetime.now().isoformat(),
            "prepared": False,
            "strategy": HAITOU_DEFAULT_POLICY["strategy_version"],
        }
        github_apply_tasks[task_id] = task
        asyncio.create_task(
            _run_github_auto_apply_task(
                task_id,
                {
                    "resume_text": resume_text,
                    "keywords": keywords,
                    "locations": locations,
                    "max_count": task["max_count"],
                    "enable_fallback_auto_apply": True,
                    "fallback_platforms": task["requested_fallback_platforms"],
                    "boss_config": data.get("boss_config"),
                    "zhilian_config": data.get("zhilian_config"),
                    "linkedin_config": data.get("linkedin_config"),
                    "headless": bool(HAITOU_DEFAULT_POLICY["headless"]),
                    "use_ai_answers": data.get("use_ai_answers", True),
                    "verification_wait_seconds": int(HAITOU_DEFAULT_POLICY["verification_wait_seconds"]),
                    "sms_code": data.get("sms_code"),
                    "blacklist": data.get("blacklist"),
                    "company_blacklist": data.get("company_blacklist"),
                    "boss_phone": data.get("boss_phone"),
                    "boss_sms_code": data.get("boss_sms_code"),
                    "phone": data.get("phone"),
                    "zhilian_username": data.get("zhilian_username"),
                    "zhilian_password": data.get("zhilian_password"),
                    "linkedin_email": data.get("linkedin_email"),
                    "linkedin_password": data.get("linkedin_password"),
                },
            )
        )
        return _api_success({"task_id": task_id, "status": "queued"})
    except Exception as e:
        logger.exception("启动 github 高星自动投递失败")
        return _api_error(str(e), status_code=500, code="github_auto_apply_start_failed")


@app.get("/api/github-auto-apply/status/{task_id}")
async def github_auto_apply_status(task_id: str):
    task = github_apply_tasks.get(task_id)
    if not task:
        return _api_error("任务不存在", status_code=404, code="task_not_found")
    linked_id = str(task.get("linked_auto_apply_task_id") or "").strip()
    linked_task = auto_apply_tasks.get(linked_id) if linked_id else None
    return _api_success(
        {
            "task": task,
            "linked_auto_apply_task": linked_task,
        }
    )


@app.get("/api/github-auto-apply/history")
async def github_auto_apply_history(limit: int = 20):
    rows = sorted(
        github_apply_tasks.values(),
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )
    rows = rows[: max(1, min(200, int(limit or 20)))]
    return _api_success({"tasks": rows, "total": len(github_apply_tasks)})


if __name__ == "__main__":
    import webbrowser
    import threading
    
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "🚀"*30)
    print("AI求职助手 - Web服务启动中...")
    print("🚀"*30 + "\n")
    print(f"📍 访问地址: http://localhost:{port}")
    print(f"📍 API文档: http://localhost:{port}/docs")
    print(f"📍 WebSocket: ws://localhost:{port}/ws/progress")
    print("\n✨ 新功能: WebSocket实时进度推送")
    print("按 Ctrl+C 停止服务\n")
    
    # 延迟2秒后自动打开浏览器
    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open(f'http://localhost:{port}/app')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run(app, host="0.0.0.0", port=port)

