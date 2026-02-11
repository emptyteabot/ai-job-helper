"""
AI求职助手 - Web界面
一个漂亮的网页界面，让您直接在浏览器中使用
"""

from fastapi import FastAPI, Request, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
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

sys.path.insert(0, os.path.dirname(__file__))

from app.core.multi_ai_debate import JobApplicationPipeline
from app.core.fast_ai_engine import fast_pipeline, HighPerformanceAIEngine
from app.core.market_driven_engine import market_driven_pipeline
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.job_searcher import JobSearcher
from app.services.real_job_service import RealJobService
from app.core.realtime_progress import progress_tracker

app = FastAPI(title="AI求职助手")

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

# 全局变量
pipeline = JobApplicationPipeline()
analyzer = ResumeAnalyzer()
searcher = JobSearcher()
real_job_service = RealJobService()  # 真实招聘数据服务

# 云端岗位缓存（内存）
cloud_jobs_cache: List[Dict[str, Any]] = []
cloud_jobs_meta: Dict[str, Any] = {
    "last_push_at": None,
    "last_received": 0,
    "last_new": 0,
}


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
    return _normalize_and_filter_jobs(matched, limit=limit)


def _search_jobs_without_browser(
    keywords: List[str], location: Optional[str], limit: int
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
        normalized = _normalize_and_filter_jobs(jobs, limit=limit)
        if normalized:
            return normalized, mode, None
    except Exception as e:
        first_error = str(e)
    else:
        first_error = None

    # Last fallback: DuckDuckGo HTML search (no key, no browser).
    # Stable public API fallback (no browser, no local extension).
    remotive_jobs = _search_jobs_remotive(keywords, location, limit=limit)
    if remotive_jobs:
        return remotive_jobs, "remotive", None

    bing_html_jobs = _search_jobs_bing_html(keywords, location, limit=limit)
    if bing_html_jobs:
        return bing_html_jobs, "bing_html", None

    # Last fallback: DuckDuckGo HTML search (no key, no browser).
    ddg_jobs = _search_jobs_duckduckgo(keywords, location, limit=limit)
    if ddg_jobs:
        return ddg_jobs, "duckduckgo", None
    return [], "cloud", first_error or "no result from no-browser providers"


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
    return host or "web"


def _normalize_ddg_redirect(href: str) -> str:
    href = (href or "").strip()
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
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
    q_parts.append("招聘 职位 site:zhipin.com OR site:liepin.com OR site:zhaopin.com OR site:51job.com")
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
        if not any(d in low for d in ("zhipin.com", "liepin.com", "zhaopin.com", "51job.com")):
            continue
        if low in seen:
            continue
        seen.add(low)
        title = re.sub(r"<[^>]+>", "", raw_title or "")
        title = html_lib.unescape(title).strip()
        out.append(
            {
                "id": f"duckduckgo_{abs(hash(low))}",
                "title": title or "招聘岗位",
                "company": "",
                "location": location or "",
                "salary": "",
                "platform": _platform_from_link(link),
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
    q_parts.append("招聘 职位 site:zhipin.com OR site:liepin.com OR site:zhaopin.com OR site:51job.com")
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
        if not any(d in low for d in ("zhipin.com", "liepin.com", "zhaopin.com", "51job.com")):
            continue
        if low in seen:
            continue
        seen.add(low)
        title = re.sub(r"<[^>]+>", "", raw_title or "")
        title = html_lib.unescape(title).strip()
        out.append(
            {
                "id": f"binghtml_{abs(hash(low))}",
                "title": title or "招聘岗位",
                "company": "",
                "location": location or "",
                "salary": "",
                "platform": _platform_from_link(link),
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
    out: List[Dict[str, Any]] = []
    for it in jobs:
        link = str(it.get("url") or "").strip()
        if not link:
            continue
        title = str(it.get("title") or "").strip()
        company = str(it.get("company_name") or "").strip()
        loc = str(it.get("candidate_required_location") or location or "").strip()
        # Optional location preference filter.
        if location and loc and location not in loc:
            continue
        out.append(
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
        if len(out) >= max(1, int(limit or 10)):
            break
    return _normalize_and_filter_jobs(out, limit=limit)

@app.get("/", response_class=HTMLResponse)
async def home():
    """主页 - 官网首页"""
    static_index = "static/index.html"
    if os.path.exists(static_index):
        with open(static_index, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>AI求职助手</h1>")

@app.get("/app", response_class=HTMLResponse)
async def app_page():
    """主应用页面"""
    app_html = "static/app.html"
    # If `static/app.html` is missing or accidentally empty, fall back to the embedded page below.
    if os.path.exists(app_html) and os.path.getsize(app_html) > 64:
        with open(app_html, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())

    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI求职助手 - 多AI协作系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
            animation: fadeInDown 0.8s ease;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: fadeInUp 0.8s ease;
        }
        
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            position: relative;
        }
        
        .step-indicator::before {
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: #e0e0e0;
            z-index: 0;
        }
        
        .step {
            flex: 1;
            text-align: center;
            position: relative;
            z-index: 1;
        }
        
        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e0e0e0;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 10px;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .step.active .step-circle {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transform: scale(1.2);
        }
        
        .step-label {
            font-size: 0.9em;
            color: #666;
        }
        
        .step.active .step-label {
            color: #667eea;
            font-weight: bold;
        }
        
        .input-section {
            margin-bottom: 30px;
        }
        
        .input-section label {
            display: block;
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        
        textarea {
            width: 100%;
            min-height: 300px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            font-family: inherit;
            resize: vertical;
            transition: border-color 0.3s;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button-group {
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        
        button {
            padding: 15px 40px;
            font-size: 1.1em;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #666;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        .ai-status {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            font-size: 0.95em;
        }
        
        .ai-status .ai-item {
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid #667eea;
            padding-left: 15px;
        }
        
        .results {
            display: none;
            margin-top: 30px;
        }
        
        .results.active {
            display: block;
        }
        
        .result-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        
        .result-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .result-card pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: inherit;
            line-height: 1.6;
        }
        
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .ai-roles {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        
        .ai-role-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.3s;
        }
        
        .ai-role-card:hover {
            transform: translateY(-5px);
        }
        
        .ai-role-card .icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .ai-role-card .name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .ai-role-card .task {
            font-size: 0.9em;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI求职助手</h1>
            <p>多AI协作系统 - 让6个AI帮您找到理想工作</p>
        </div>
        
        <div class="main-card">
            <div class="step-indicator">
                <div class="step active" id="step1">
                    <div class="step-circle">1</div>
                    <div class="step-label">上传简历</div>
                </div>
                <div class="step" id="step2">
                    <div class="step-circle">2</div>
                    <div class="step-label">AI分析</div>
                </div>
                <div class="step" id="step3">
                    <div class="step-circle">3</div>
                    <div class="step-label">优化简历</div>
                </div>
                <div class="step" id="step4">
                    <div class="step-circle">4</div>
                    <div class="step-label">面试准备</div>
                </div>
            </div>
            
            <div class="ai-roles">
                <div class="ai-role-card">
                    <div class="icon">👔</div>
                    <div class="name">职业规划师</div>
                    <div class="task">分析优势定位</div>
                </div>
                <div class="ai-role-card">
                    <div class="icon">🔍</div>
                    <div class="name">招聘专家</div>
                    <div class="task">搜索匹配岗位</div>
                </div>
                <div class="ai-role-card">
                    <div class="icon">✍️</div>
                    <div class="name">简历优化师</div>
                    <div class="task">改写简历内容</div>
                </div>
                <div class="ai-role-card">
                    <div class="icon">✅</div>
                    <div class="name">质量检查官</div>
                    <div class="task">审核并改进</div>
                </div>
                <div class="ai-role-card">
                    <div class="icon">🎓</div>
                    <div class="name">面试教练</div>
                    <div class="task">面试辅导</div>
                </div>
                <div class="ai-role-card">
                    <div class="icon">🎭</div>
                    <div class="name">模拟面试官</div>
                    <div class="task">模拟面试</div>
                </div>
            </div>
            
            <div class="input-section" id="inputSection">
                <label>📄 上传简历或输入内容：</label>
                
                <!-- 文件上传区域 -->
                <div style="margin-bottom: 20px;">
                    <input type="file" id="fileInput" accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.bmp,.gif" style="display: none;" onchange="handleFileUpload(event)">
                    <button class="btn-secondary" onclick="document.getElementById('fileInput').click()" style="width: 100%; padding: 20px; font-size: 1em;">
                        📎 点击上传简历文件（支持PDF、Word、TXT、图片）
                    </button>
                    <div id="uploadStatus" style="margin-top: 10px; text-align: center; color: #667eea; font-weight: bold;"></div>
                </div>
                
                <div style="text-align: center; margin: 20px 0; color: #999;">或者</div>
                
                <textarea id="resumeInput" placeholder="直接输入您的简历内容：
- 姓名、学历、工作经验
- 技能清单（编程语言、框架、工具等）
- 项目经验
- 求职意向

示例：
姓名：张三
学历：本科 - 计算机科学
工作经验：3年Python开发
技能：Python, Django, MySQL, Redis
项目：电商后台系统、数据分析平台
求职意向：Python后端开发工程师"></textarea>
                
                <div class="button-group" style="margin-top: 20px;">
                    <button class="btn-secondary" onclick="loadExample()">使用示例简历</button>
                    <button class="btn-primary" onclick="startProcess()">🚀 开始AI协作</button>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <h3>🤖 AI团队正在协作中...</h3>
                <p>6个AI正在依次工作，预计需要1-2分钟</p>
                <div class="ai-status" id="aiStatus"></div>
            </div>
            
            <div class="results" id="results">
                <h2 style="text-align: center; color: #667eea; margin-bottom: 30px;">🎉 AI协作完成！</h2>
                
                <div class="result-card">
                    <h3>📊 职业分析报告</h3>
                    <pre id="careerAnalysis"></pre>
                </div>
                
                <div class="result-card">
                    <h3>🎯 推荐岗位列表</h3>
                    <pre id="jobRecommendations"></pre>
                </div>
                
                <div class="result-card">
                    <h3>✍️ 优化后的简历</h3>
                    <pre id="optimizedResume"></pre>
                </div>
                
                <div class="result-card">
                    <h3>🎓 面试准备指南</h3>
                    <pre id="interviewPrep"></pre>
                </div>
                
                <div class="result-card">
                    <h3>🎭 模拟面试问答</h3>
                    <pre id="mockInterview"></pre>
                </div>
                
                <div class="button-group" style="margin-top: 30px;">
                    <button class="btn-secondary" onclick="location.reload()">重新开始</button>
                    <button class="btn-primary" onclick="downloadResults()">📥 下载结果</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.textContent = '📤 正在上传和解析文件...';
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || '上传失败');
                }
                
                const data = await response.json();
                
                // 显示上传成功
                statusDiv.textContent = `✅ 文件上传成功：${data.filename}`;
                statusDiv.style.color = '#27ae60';
                
                // 等待1秒后自动开始AI处理
                setTimeout(() => {
                    statusDiv.textContent = '🚀 正在启动AI协作...';
                    statusDiv.style.color = '#667eea';
                    
                    // 自动开始处理
                    processResumeText(data.resume_text);
                }, 1000);
                
            } catch (error) {
                statusDiv.textContent = `❌ ${error.message}`;
                statusDiv.style.color = '#e74c3c';
            }
        }
        
        async function processResumeText(resumeText) {
            // 隐藏输入区，显示加载动画
            document.getElementById('inputSection').style.display = 'none';
            document.getElementById('loading').classList.add('active');
            document.getElementById('step2').classList.add('active');
            
            try {
                // 调用后端API
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ resume: resumeText })
                });
                
                if (!response.ok) {
                    throw new Error('处理失败');
                }
                
                const data = await response.json();
                
                // 显示结果
                document.getElementById('loading').classList.remove('active');
                document.getElementById('results').classList.add('active');
                document.getElementById('step3').classList.add('active');
                document.getElementById('step4').classList.add('active');
                
                document.getElementById('careerAnalysis').textContent = data.career_analysis;
                document.getElementById('jobRecommendations').textContent = data.job_recommendations;
                document.getElementById('optimizedResume').textContent = data.optimized_resume;
                document.getElementById('interviewPrep').textContent = data.interview_prep;
                document.getElementById('mockInterview').textContent = data.mock_interview;
                
            } catch (error) {
                alert('处理出错：' + error.message);
                location.reload();
            }
        }
        
        function loadExample() {
            document.getElementById('resumeInput').value = `姓名：李明
学历：本科 - 软件工程
工作经验：3年Python开发经验

技能清单：
- 编程语言: Python, JavaScript, SQL
- 后端框架: Django, Flask, FastAPI
- 数据库: MySQL, Redis, MongoDB
- 前端: React, Vue.js, HTML/CSS
- 工具: Docker, Git, Linux

项目经验：
1. 电商后台管理系统
   - 使用Django + MySQL开发
   - 实现商品管理、订单处理、用户权限等功能
   - 日均处理订单5000+

2. 数据分析平台
   - 使用Python + Pandas进行数据处理
   - 开发可视化报表系统
   - 支持实时数据监控

3. RESTful API服务
   - 使用FastAPI开发高性能API
   - 集成Redis缓存，响应时间<100ms
   - 日均请求量100万+

求职意向：Python后端开发工程师 / 全栈开发工程师
期望薪资：20-35K
工作地点：北京、上海、杭州`;
        }
        
        async function startProcess() {
            const resume = document.getElementById('resumeInput').value.trim();
            
            if (!resume) {
                alert('请先输入简历内容或上传文件！');
                return;
            }
            
            // 调用统一的处理函数
            processResumeText(resume);
        }
        
        function downloadResults() {
            // 下载所有结果为文本文件
            const results = {
                '职业分析': document.getElementById('careerAnalysis').textContent,
                '推荐岗位': document.getElementById('jobRecommendations').textContent,
                '优化后简历': document.getElementById('optimizedResume').textContent,
                '面试准备': document.getElementById('interviewPrep').textContent,
                '模拟面试': document.getElementById('mockInterview').textContent
            };
            
            let content = '';
            for (const [title, text] of Object.entries(results)) {
                content += `\n${'='.repeat(60)}\n${title}\n${'='.repeat(60)}\n\n${text}\n\n`;
            }
            
            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'AI求职助手-完整结果.txt';
            a.click();
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
    """

@app.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)):
    """上传简历文件（支持PDF、Word、TXT、图片）"""
    try:
        # 检查文件类型
        allowed_types = ['.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png', '.bmp', '.gif']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_types:
            return JSONResponse({
                "error": f"不支持的文件格式。支持：PDF、Word、TXT、图片（JPG/PNG等）"
            }, status_code=400)
        
        # 读取文件内容
        content = await file.read()
        resume_text = ""
        
        try:
            # 解析文件
            if file_ext == '.txt':
                # 文本文件
                try:
                    resume_text = content.decode('utf-8')
                except:
                    resume_text = content.decode('gbk', errors='ignore')
                    
            elif file_ext == '.pdf':
                # PDF文件
                try:
                    import PyPDF2
                    import io
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            resume_text += text + "\n"
                except Exception as e:
                    return JSONResponse({
                        "error": f"PDF解析失败: {str(e)}。请确保PDF不是扫描件，或上传图片格式。"
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
                    import pytesseract
                    import io
                    
                    # 打开图片
                    image = Image.open(io.BytesIO(content))
                    
                    # OCR识别（支持中英文）
                    resume_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                    
                    if not resume_text.strip():
                        return JSONResponse({
                            "error": "图片识别失败，未能提取到文字。请确保图片清晰，或尝试其他格式。"
                        }, status_code=500)
                        
                except ImportError:
                    return JSONResponse({
                        "error": "图片OCR功能未安装。正在安装依赖，请稍后重试..."
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
            return JSONResponse({"error": "简历内容不能为空"}, status_code=400)
        
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
        
        # Replace the old hardcoded job list with real, actionable job links.
        # Priority: cloud(cache) -> cloud-safe real-time search (no browser).
        def _format_real_jobs(jobs, mode: str) -> str:
            if not jobs:
                return (
                    '【推荐岗位】（当前暂无可用岗位）\n\n'
                    '排查建议：\n'
                    '1. 检查云端缓存：访问 /api/crawler/status 是否为 empty。\n'
                    '2. 当前已启用无浏览器搜索回退（baidu/bing/brave/jooble）。\n'
                    '3. 若搜索引擎触发风控，可切换 API 数据源或稍后重试。\n\n'
                    '注意：系统不会回退到演示岗位；无真实数据时只展示该提示。\n'
                )

            heading = '【推荐岗位】（真实市场数据）'
            if mode == 'openclaw':
                heading = '【推荐岗位】（来自 Boss 直聘实时数据，OpenClaw）'
            elif mode == 'cloud':
                heading = '【推荐岗位】（来自 Boss 直聘云端缓存）'
            elif mode in ('baidu', 'bing', 'brave'):
                heading = f'【推荐岗位】（来自搜索引擎 {mode}）'
            elif mode == 'remotive':
                heading = '【推荐岗位】（来自 Remotive 公共招聘 API）'
            elif mode == 'bing_html':
                heading = '【推荐岗位】（来自 Bing 无浏览器搜索）'
            elif mode == 'duckduckgo':
                heading = '【推荐岗位】（来自 DuckDuckGo 无浏览器搜索）'
            elif mode == 'jooble':
                heading = '【推荐岗位】（来自 Jooble API）'

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
            kw = seed_keywords[:10]
            loc = seed_location

            if cfg_mode == 'cloud' or cloud_jobs_cache:
                cached = _filter_cloud_cache_by_query(kw, loc, limit=10)
                if cached:
                    return cached, 'cloud'
                # Cache empty/insufficient: fallback to cloud-safe real-time providers.
                fallback_jobs, fallback_mode, _ = _search_jobs_without_browser(kw, loc, limit=10)
                return fallback_jobs, fallback_mode

            try:
                jobs = _normalize_and_filter_jobs(
                    real_job_service.search_jobs(keywords=kw, location=loc, limit=10),
                    limit=10,
                )
                mode = (real_job_service.get_statistics() or {}).get('provider_mode', '') or cfg_mode
                return jobs[:10], mode
            except Exception:
                return [], cfg_mode

        real_jobs, real_mode = await _get_real_jobs_for_recommendation()
        results['job_recommendations'] = _format_real_jobs(real_jobs, real_mode)
        provider_mode = real_mode

        # 完成
        await progress_tracker.complete()
        await progress_tracker.add_ai_message("系统", "🎉 市场分析完成！")
        
        return JSONResponse({
            "career_analysis": results['market_analysis'],
            "job_recommendations": results['job_recommendations'],
            "optimized_resume": results['optimized_resume'],
            "interview_prep": results['interview_prep'],
            "mock_interview": results.get('salary_analysis', '')
            ,
            "job_provider_mode": provider_mode,
            "boss_seed": {
                "keywords": seed_keywords,
                "location": seed_location,
            },
        })
        
    except Exception as e:
        await progress_tracker.error(f"处理出错: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/health")
async def health_check():
    """健康检查"""
    stats = real_job_service.get_statistics()
    
    # 检查OpenClaw状态
    openclaw_status = None
    if stats.get("provider_mode") == "openclaw":
        from app.services.job_providers.openclaw_browser_provider import OpenClawBrowserProvider
        openclaw = OpenClawBrowserProvider()
        openclaw_status = openclaw.health_check()
    
    return {
        "status": "ok",
        "message": "AI求职助手运行正常",
        "job_database": stats,
        "openclaw": openclaw_status,
        "config": {
            "job_data_provider": os.getenv("JOB_DATA_PROVIDER", "auto"),
            "cloud_cache_total": len(cloud_jobs_cache),
            "cloud_last_push_at": cloud_jobs_meta.get("last_push_at"),
            "no_browser_fallback_enabled": True,
        },
    }



@app.get("/api/version")
async def version():
    """Expose basic build metadata for debugging deployments."""
    return {
        "job_data_provider": os.getenv("JOB_DATA_PROVIDER", "auto"),
        "railway_git_commit_sha": os.getenv("RAILWAY_GIT_COMMIT_SHA"),
        "github_sha": os.getenv("GITHUB_SHA"),
    }

@app.get("/api/jobs/search")
async def search_jobs(
    keywords: str = None,
    location: str = None,
    salary_min: int = None,
    experience: str = None,
    limit: int = 50
):
    """搜索真实岗位"""
    try:
        cfg_mode = os.getenv("JOB_DATA_PROVIDER", "auto").strip().lower()
        n = int(limit) if limit is not None else 50
        n = max(1, min(n, 100))
        keyword_list = keywords.split(",") if keywords else []
        kw = [k.strip() for k in keyword_list if k and k.strip()]

        # Cloud mode: prefer crawler cache; fallback to cloud-safe real-time providers.
        if cfg_mode == "cloud" or cloud_jobs_cache:
            jobs = _filter_cloud_cache_by_query(kw, location, limit=n)
            warning = None
            mode = "cloud"
            if not jobs:
                fallback_jobs, fallback_mode, fallback_err = _search_jobs_without_browser(kw, location, limit=n)
                jobs = fallback_jobs
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
            return JSONResponse({
                "success": True,
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

        jobs = real_job_service.search_jobs(
            keywords=kw,
            location=location,
            salary_min=salary_min,
            experience=experience,
            limit=n,
            progress_callback=progress_cb,
        )
        jobs = _normalize_and_filter_jobs(jobs, limit=n)
        return JSONResponse({
            "success": True,
            "total": len(jobs),
            "jobs": jobs,
            "provider_mode": (real_job_service.get_statistics() or {}).get("provider_mode", cfg_mode),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

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
        return JSONResponse(result)
    except Exception as e:
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
        return JSONResponse({
            "success": True,
            "total": len(results),
            "results": results
        })
    except Exception as e:
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

