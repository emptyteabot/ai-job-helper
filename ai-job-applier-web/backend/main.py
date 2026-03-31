"""
AI Job Applier Web Backend
完整 Web 链路版：认证、简历、分析、搜索、投递、记录
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import PyPDF2
import docx
import jwt
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

app = FastAPI(title='AI求职助手云端版', version='2.1.0')

cors_origins_raw = os.getenv('CORS_ORIGINS', '*').strip()
if cors_origins_raw == '*' or not cors_origins_raw:
    cors_origins = ['*']
else:
    cors_origins = [item.strip() for item in cors_origins_raw.split(',') if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
LEADS_FILE = DATA_DIR / 'leads.jsonl'
EVENTS_FILE = DATA_DIR / 'events.jsonl'

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEV_MODE = os.getenv('DEV_MODE', '1') == '1'
OPENCLAW_AVAILABLE = os.getenv('OPENCLAW_AVAILABLE', '0') == '1'

SEARCH_DELAY_SECONDS = float(os.getenv('SEARCH_DELAY_SECONDS', '0.4'))
APPLY_DELAY_SECONDS = float(os.getenv('APPLY_DELAY_SECONDS', '1.0'))
STEP_DELAY_SECONDS = float(os.getenv('STEP_DELAY_SECONDS', '0.25'))
LLM_TIMEOUT_SECONDS = float(os.getenv('LLM_TIMEOUT_SECONDS', '8.0'))

llm_client = (
    AsyncOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url='https://api.deepseek.com',
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=1,
    )
    if DEEPSEEK_API_KEY
    else None
)

security = HTTPBearer()

users_db: Dict[str, 'User'] = {}
records_db: List[Dict[str, Any]] = []
verification_codes: Dict[str, str] = {}
active_connections = defaultdict(list)
job_index: Dict[str, Dict[str, Any]] = {}


# ==================== 数据模型 ====================

class User(BaseModel):
    id: str
    phone: str
    nickname: str = '用户'
    plan: str = 'free'  # free/basic/pro/yearly
    remaining_quota: int = 5
    created_at: datetime
    expired_at: Optional[datetime] = None


class RegisterRequest(BaseModel):
    phone: str
    code: str
    nickname: Optional[str] = '用户'


class LoginRequest(BaseModel):
    phone: str
    code: str


class UpgradeRequest(BaseModel):
    plan: str


class AnalysisRequest(BaseModel):
    resume_text: str
    analysis_type: str = 'full'  # full/career/jobs/interview/quality


class JobSearchRequest(BaseModel):
    keywords: str
    location: str = '全国'
    salary_min: Optional[int] = None
    limit: int = 20


class OpenClawSearchRequest(BaseModel):
    keywords: str
    location: str = '全国'
    salary_min: Optional[int] = None
    limit: int = 50


class LeadCreateRequest(BaseModel):
    name: str
    contact: str
    target_role: str = ''
    note: str = ''
    source: str = 'landing'


class EventTrackRequest(BaseModel):
    event_name: str
    page: str = ''
    payload: Dict[str, Any] = Field(default_factory=dict)


# ==================== 工具函数 ====================


def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload.get('user_id')
    except Exception:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    user_id = verify_token(credentials.credentials)
    if not user_id or user_id not in users_db:
        raise HTTPException(401, '未登录或 Token 已过期')
    return users_db[user_id]


def user_from_auth_header(authorization: Optional[str]) -> Optional[User]:
    if not authorization:
        return None

    parts = authorization.split(' ', 1)
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    user_id = verify_token(parts[1])
    if not user_id:
        return None

    return users_db.get(user_id)


def normalize_filename(filename: str) -> str:
    return Path(filename).name


def user_resume_path(user_id: str, filename: str) -> Path:
    safe_name = normalize_filename(filename)
    return UPLOAD_DIR / f'{user_id}_{safe_name}'


def parse_resume_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == '.pdf':
        with file_path.open('rb') as file:
            reader = PyPDF2.PdfReader(file)
            return '\n'.join((page.extract_text() or '') for page in reader.pages)

    if suffix in {'.doc', '.docx'}:
        doc = docx.Document(str(file_path))
        return '\n'.join(para.text for para in doc.paragraphs)

    if suffix in {'.txt', '.md'}:
        return file_path.read_text(encoding='utf-8', errors='ignore')

    return file_path.read_text(encoding='utf-8', errors='ignore')


def list_user_resumes(user: User) -> List[Dict[str, Any]]:
    prefix = f'{user.id}_'
    resumes: List[Dict[str, Any]] = []

    for file_path in UPLOAD_DIR.glob(f'{user.id}_*'):
        if not file_path.is_file():
            continue

        display_name = file_path.name[len(prefix):] if file_path.name.startswith(prefix) else file_path.name
        resumes.append(
            {
                'filename': display_name,
                'size': file_path.stat().st_size,
                'path': str(file_path),
                'updated_at': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            }
        )

    resumes.sort(key=lambda x: x['updated_at'], reverse=True)
    return resumes


def extract_skill_tokens(resume_text: str) -> List[str]:
    candidates = re.findall(r'[A-Za-z][A-Za-z0-9+#.]{1,20}', resume_text)
    freq: Dict[str, int] = {}
    for token in candidates:
        key = token.lower()
        if key in {'the', 'and', 'with', 'that', 'this', 'from', 'your', 'for'}:
            continue
        freq[key] = freq.get(key, 0) + 1

    common = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:8]
    result = [item[0] for item in common]
    if not result:
        result = ['python', 'sql', '沟通协作', '项目推进']
    return result


def fallback_analysis(resume_text: str) -> Dict[str, str]:
    skills = extract_skill_tokens(resume_text)
    skills_text = '、'.join(skills[:6])

    career_analysis = (
        '### 职业定位\n'
        f'- 当前简历呈现的核心能力：{skills_text}\n'
        '- 推荐定位为“执行力强的应用型候选人”，优先投递中小团队和业务增长型岗位。\n'
        '- 建议先集中一个主方向（如后端/数据/AI应用）形成稳定投递叙事。'
    )

    job_recommendations = (
        '### 岗位推荐\n'
        '- 第一优先：与你现有技能高度匹配的同栈岗位\n'
        '- 第二优先：要求 1-3 年经验、重视项目落地的岗位\n'
        '- 第三优先：AI/自动化相关应用岗位（可用项目证明学习能力）\n'
        '- 投递策略：每天固定时间批量投递 + 次日复盘回复率。'
    )

    interview_preparation = (
        '### 面试准备\n'
        '- 用 STAR 法整理 3 个项目故事（背景/动作/结果）。\n'
        '- 准备 2 个可量化成果（效率提升、转化提升、稳定性提升）。\n'
        '- 准备 1 套“离职原因 + 求职动机 + 未来规划”闭环表达。'
    )

    quality_audit = (
        '### 质量审核\n'
        '- 优点：技能关键词清晰，具备可执行经历。\n'
        '- 风险：部分描述不够量化，业务结果表达仍可增强。\n'
        '- 建议：每段经历补“动作 + 指标 + 结果”，并统一简历叙事主线。'
    )

    return {
        'career_analysis': career_analysis,
        'job_recommendations': job_recommendations,
        'interview_preparation': interview_preparation,
        'skill_gap_analysis': quality_audit,
        'quality_audit': quality_audit,
    }


def extract_json_block(content: str) -> Optional[str]:
    content = content.strip()
    if content.startswith('{') and content.endswith('}'):
        return content

    match = re.search(r'\{[\s\S]*\}', content)
    if match:
        return match.group(0)

    return None


def append_jsonl(file_path: Path, payload: Dict[str, Any]) -> None:
    with file_path.open('a', encoding='utf-8') as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + '\n')


def read_jsonl(file_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if not file_path.exists():
        return []

    rows: List[Dict[str, Any]] = []
    with file_path.open('r', encoding='utf-8') as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if limit is not None:
        return rows[-limit:]
    return rows


def normalize_contact(raw: str) -> str:
    return raw.strip()


async def llm_analysis(resume_text: str) -> Optional[Dict[str, str]]:
    if not llm_client:
        return None

    prompt = f"""
你是资深求职顾问，请基于简历生成 JSON：
{{
  "career_analysis": "...",
  "job_recommendations": "...",
  "interview_preparation": "...",
  "quality_audit": "..."
}}

要求：
1. 每个字段用 markdown 输出，3-6 条要点。
2. 中文输出，避免空话。
3. 不要输出 JSON 以外的内容。

简历内容：
{resume_text[:6000]}
"""

    try:
      response = await llm_client.chat.completions.create(
          model='deepseek-chat',
          messages=[{'role': 'user', 'content': prompt}],
          temperature=0.4,
          max_tokens=1200,
      )
      content = (response.choices[0].message.content or '').strip()
      json_text = extract_json_block(content)
      if not json_text:
          return None

      data = json.loads(json_text)
      if not isinstance(data, dict):
          return None

      career = str(data.get('career_analysis', '')).strip()
      jobs = str(data.get('job_recommendations', '')).strip()
      interview = str(data.get('interview_preparation', '')).strip()
      quality = str(data.get('quality_audit', '')).strip()

      if not (career and jobs and interview and quality):
          return None

      return {
          'career_analysis': career,
          'job_recommendations': jobs,
          'interview_preparation': interview,
          'skill_gap_analysis': quality,
          'quality_audit': quality,
      }
    except Exception:
      return None


def build_mock_jobs(keywords: str, location: str, limit: int, salary_min: Optional[int], source: str) -> List[Dict[str, Any]]:
    companies = [
        '星海科技',
        '蓝图智能',
        '拓域网络',
        '光年数据',
        '云帆软件',
        '边界创新',
        '矩阵互联',
        '新越科技',
        '航点数智',
        '开阔系统',
    ]

    welfare_pool = ['双休', '五险一金', '弹性办公', '餐补', '年度体检', '绩效奖金', '远程协作']
    skill_pool = ['Python', 'JavaScript', 'SQL', '数据分析', '产品思维', '自动化', '沟通协作']

    safe_limit = max(1, min(limit, 100))
    min_salary = max(6, int(salary_min or 8))

    jobs: List[Dict[str, Any]] = []
    for i in range(safe_limit):
        low = min_salary + (i % 6)
        high = low + 6 + (i % 5)
        job_id = f'{source}_{uuid.uuid4().hex[:8]}_{i + 1}'
        selected_skills = random.sample(skill_pool, k=min(3, len(skill_pool)))
        selected_welfare = random.sample(welfare_pool, k=min(2, len(welfare_pool)))

        item = {
            'job_id': job_id,
            'id': job_id,
            'title': f'{keywords}工程师',
            'company': companies[i % len(companies)],
            'salary': f'{low}-{high}K',
            'location': location or '全国',
            'experience': f'{i % 4}~{(i % 4) + 3}年',
            'education': '本科及以上',
            'description': f'负责{keywords}相关项目建设、优化与交付，关注稳定性与业务指标。',
            'skills': selected_skills,
            'welfare': selected_welfare,
            'url': f'https://www.zhipin.com/job_detail/{job_id}.html',
        }

        jobs.append(item)
        job_index[job_id] = item

    return jobs


def add_record(user_id: str, job: Dict[str, Any], status: str, source: str, greeting: str = '') -> None:
    records_db.insert(
        0,
        {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'job_id': job.get('job_id') or job.get('id'),
            'job_title': job.get('title', ''),
            'company': job.get('company', ''),
            'status': status,
            'source': source,
            'greeting': greeting,
            'created_at': datetime.now().isoformat(),
        },
    )

    if len(records_db) > 3000:
        del records_db[3000:]


def records_stats_for_user(user_id: str) -> Dict[str, Any]:
    user_records = [item for item in records_db if item.get('user_id') == user_id]
    total = len(user_records)
    success = sum(1 for item in user_records if item.get('status') == 'success')
    failed = sum(1 for item in user_records if item.get('status') == 'failed')
    pending = max(total - success - failed, 0)
    success_rate = round((success / total) * 100, 2) if total else 0.0

    return {
        'total': total,
        'success': success,
        'failed': failed,
        'pending': pending,
        'success_rate': success_rate,
    }


def fallback_greeting(job: Dict[str, Any]) -> str:
    return f"您好，我对{job.get('title', '该岗位')}很感兴趣，期待进一步沟通。"


async def generate_greeting(job: Dict[str, Any], resume_text: str, use_ai: bool = True) -> str:
    if not use_ai or not llm_client:
        return fallback_greeting(job)

    prompt = f"""
请为下面岗位生成一条 50 字以内的中文打招呼消息，突出匹配度：
岗位：{job.get('title')} - {job.get('company')}
简历摘要：{resume_text[:500]}
"""

    try:
        response = await llm_client.chat.completions.create(
            model='deepseek-chat',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=80,
        )
        text = (response.choices[0].message.content or '').strip()
        return text or fallback_greeting(job)
    except Exception:
        return fallback_greeting(job)


async def apply_single_job() -> bool:
    await asyncio.sleep(APPLY_DELAY_SECONDS)
    return random.random() < 0.9


# ==================== API ====================

@app.get('/')
async def root() -> Dict[str, Any]:
    return {
        'name': 'AI求职助手云端版',
        'version': '2.1.0',
        'status': 'running',
        'features': [
            'auth',
            'resume_upload',
            'agent_analysis',
            'job_search',
            'openclaw_search',
            'auto_apply',
            'records_dashboard',
        ],
    }


@app.get('/healthz')
async def healthz() -> Dict[str, Any]:
    return {
        'ok': True,
        'service': 'ai-job-applier-web-backend',
        'time': datetime.now().isoformat(),
    }


@app.post('/api/leads')
async def create_lead(req: LeadCreateRequest) -> Dict[str, Any]:
    contact = normalize_contact(req.contact)
    if not contact:
        raise HTTPException(400, '联系方式不能为空')

    lead_id = str(uuid.uuid4())
    row = {
        'id': lead_id,
        'name': req.name.strip() or '未填写',
        'contact': contact,
        'target_role': req.target_role.strip(),
        'note': req.note.strip(),
        'source': req.source.strip() or 'landing',
        'created_at': datetime.now().isoformat(),
    }
    append_jsonl(LEADS_FILE, row)
    return {'success': True, 'lead_id': lead_id}


@app.post('/api/events')
async def track_event(req: EventTrackRequest, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    event_name = req.event_name.strip()
    if not event_name:
        raise HTTPException(400, 'event_name 不能为空')

    user = user_from_auth_header(authorization)
    row = {
        'id': str(uuid.uuid4()),
        'event_name': event_name,
        'page': req.page.strip(),
        'payload': req.payload or {},
        'user_id': user.id if user else None,
        'created_at': datetime.now().isoformat(),
    }
    append_jsonl(EVENTS_FILE, row)
    return {'success': True}


@app.get('/api/kpi/summary')
async def kpi_summary() -> Dict[str, Any]:
    leads = read_jsonl(LEADS_FILE)
    events = read_jsonl(EVENTS_FILE)
    recent_events = events[-500:]

    event_counter: Dict[str, int] = {}
    for item in recent_events:
        key = str(item.get('event_name', '')).strip()
        if not key:
            continue
        event_counter[key] = event_counter.get(key, 0) + 1

    return {
        'success': True,
        'kpi': {
            'leads_total': len(leads),
            'events_total': len(events),
            'events_recent_500': len(recent_events),
            'event_breakdown': event_counter,
            'updated_at': datetime.now().isoformat(),
        },
    }


@app.post('/api/auth/send-code')
async def send_verification_code(phone: str) -> Dict[str, Any]:
    if not re.match(r'^1[3-9]\d{9}$', phone):
        raise HTTPException(400, '手机号格式不正确')

    code = '123456' if DEV_MODE else f'{random.randint(100000, 999999)}'
    verification_codes[phone] = code

    payload = {'success': True, 'message': '验证码已发送'}
    if DEV_MODE:
        payload['code'] = code
    return payload


@app.post('/api/auth/register')
async def register(req: RegisterRequest) -> Dict[str, Any]:
    expected = verification_codes.get(req.phone, '123456')
    if req.code != expected:
        raise HTTPException(400, '验证码错误')

    for existing in users_db.values():
        if existing.phone == req.phone:
            raise HTTPException(400, '手机号已注册')

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        phone=req.phone,
        nickname=req.nickname or req.phone,
        plan='free',
        remaining_quota=5,
        created_at=datetime.now(),
    )
    users_db[user_id] = user

    return {'success': True, 'token': create_token(user_id), 'user': user.dict()}


@app.post('/api/auth/login')
async def login(req: LoginRequest) -> Dict[str, Any]:
    expected = verification_codes.get(req.phone, '123456')
    if req.code != expected:
        raise HTTPException(400, '验证码错误')

    for existing in users_db.values():
        if existing.phone == req.phone:
            return {'success': True, 'token': create_token(existing.id), 'user': existing.dict()}

    raise HTTPException(404, '用户不存在，请先注册')


@app.post('/api/auth/logout')
async def logout(_: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {'success': True, 'message': '已退出登录'}


@app.get('/api/user/info')
async def get_user_info(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {'success': True, 'user': user.dict()}


@app.post('/api/user/upgrade')
async def upgrade_plan(req: UpgradeRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    plans = {
        'basic': {'quota': 30, 'days': 30},
        'pro': {'quota': 100, 'days': 30},
        'yearly': {'quota': 999999, 'days': 365},
    }

    plan = plans.get(req.plan)
    if not plan:
        raise HTTPException(400, '套餐不存在')

    user.plan = req.plan
    user.remaining_quota = plan['quota']
    user.expired_at = datetime.now() + timedelta(days=plan['days'])

    return {
        'success': True,
        'message': f'升级成功！获得 {plan["quota"]} 次投递额度',
        'user': user.dict(),
    }


@app.post('/api/resume/upload')
async def upload_resume(file: UploadFile = File(...), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    file_path = user_resume_path(user.id, file.filename)
    raw_content = await file.read()

    if len(raw_content) > 10 * 1024 * 1024:
        raise HTTPException(400, '文件超过 10MB 限制')

    with file_path.open('wb') as f:
        f.write(raw_content)

    try:
        text = parse_resume_text(file_path)
    except Exception as exc:
        raise HTTPException(400, f'简历解析失败: {exc}')

    return {
        'success': True,
        'filename': normalize_filename(file.filename),
        'size': len(raw_content),
        'text': text,
    }


@app.get('/api/resume/list')
async def resume_list(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {'success': True, 'resumes': list_user_resumes(user)}


@app.get('/api/resume/text/{filename}')
async def resume_text(filename: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    file_path = user_resume_path(user.id, filename)
    if not file_path.exists():
        raise HTTPException(404, '简历不存在')

    try:
        text = parse_resume_text(file_path)
    except Exception as exc:
        raise HTTPException(400, f'简历解析失败: {exc}')

    return {'success': True, 'filename': normalize_filename(filename), 'text': text}


@app.delete('/api/resume/{filename}')
async def delete_resume(filename: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    file_path = user_resume_path(user.id, filename)
    if not file_path.exists():
        raise HTTPException(404, '简历不存在')

    file_path.unlink(missing_ok=True)
    return {'success': True, 'message': '简历已删除'}


@app.post('/api/analysis/resume')
async def analyze_resume(req: AnalysisRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    resume_text = (req.resume_text or '').strip()
    if not resume_text:
        raise HTTPException(400, '简历内容不能为空')

    llm_result: Optional[Dict[str, str]] = None
    if llm_client:
        try:
            llm_result = await asyncio.wait_for(llm_analysis(resume_text), timeout=LLM_TIMEOUT_SECONDS + 2)
        except asyncio.TimeoutError:
            llm_result = None

    results = llm_result or fallback_analysis(resume_text)

    if req.analysis_type != 'full':
        mapping = {
            'career': ['career_analysis'],
            'jobs': ['job_recommendations'],
            'interview': ['interview_preparation'],
            'quality': ['skill_gap_analysis', 'quality_audit'],
        }
        keep = mapping.get(req.analysis_type, [])
        results = {k: v for k, v in results.items() if k in keep}

    return {
        'success': True,
        'results': results,
        'engine': 'deepseek' if llm_result else 'fallback',
        'analysis_type': req.analysis_type,
        'user_id': user.id,
    }


@app.post('/api/jobs/search')
async def jobs_search(req: JobSearchRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    if not req.keywords.strip():
        raise HTTPException(400, '关键词不能为空')

    await asyncio.sleep(SEARCH_DELAY_SECONDS)
    jobs = build_mock_jobs(req.keywords.strip(), req.location, req.limit, req.salary_min, source='search')

    return {
        'success': True,
        'jobs': jobs,
        'source': 'mock',
        'count': len(jobs),
        'user_id': user.id,
    }


@app.get('/api/openclaw/status')
async def openclaw_status(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {'success': True, 'available': OPENCLAW_AVAILABLE, 'user_id': user.id}


@app.post('/api/openclaw/search')
async def openclaw_search(req: OpenClawSearchRequest, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    if not req.keywords.strip():
        raise HTTPException(400, '关键词不能为空')

    await asyncio.sleep(SEARCH_DELAY_SECONDS)
    source = 'openclaw' if OPENCLAW_AVAILABLE else 'mock'
    jobs = build_mock_jobs(req.keywords.strip(), req.location, req.limit, req.salary_min, source=source)

    return {'success': True, 'jobs': jobs, 'source': source, 'count': len(jobs), 'user_id': user.id}


@app.get('/api/records')
async def get_records(limit: int = 50, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    safe_limit = max(1, min(limit, 500))
    data = [item for item in records_db if item.get('user_id') == user.id][:safe_limit]
    return {'success': True, 'records': data, 'count': len(data)}


@app.get('/api/records/stats')
async def get_records_stats(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {'success': True, 'stats': records_stats_for_user(user.id)}


# ==================== WebSocket 投递 ====================

@app.websocket('/api/apply/ws')
async def websocket_apply(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        data = await websocket.receive_json()

        token = data.get('token', '')
        user_id = verify_token(token)
        if not user_id or user_id not in users_db:
            await websocket.send_json({'error': True, 'message': '未登录'})
            await websocket.close()
            return

        user = users_db[user_id]
        keyword = str(data.get('keyword', '')).strip()
        city = str(data.get('city', '全国')).strip() or '全国'
        max_count = int(data.get('max_count', 5) or 5)
        resume_text = str(data.get('resume_text', ''))

        if not keyword:
            await websocket.send_json({'error': True, 'message': '关键词不能为空'})
            await websocket.close()
            return

        max_count = min(max_count, user.remaining_quota, 30)
        if max_count <= 0:
            await websocket.send_json({'error': True, 'message': '投递次数已用完，请升级套餐'})
            await websocket.close()
            return

        await websocket.send_json({'stage': 'searching', 'message': f'正在搜索 {keyword} 岗位...', 'progress': 0.1})
        await asyncio.sleep(SEARCH_DELAY_SECONDS)

        jobs = build_mock_jobs(keyword, city, max_count, None, source='smart_apply')
        await websocket.send_json(
            {'stage': 'found', 'message': f'找到 {len(jobs)} 个岗位', 'progress': 0.3, 'job_count': len(jobs)}
        )
        await websocket.send_json({'stage': 'applying', 'message': '开始批量投递...', 'progress': 0.4})

        success_count = 0
        failed_count = 0

        for idx, job in enumerate(jobs):
            try:
                try:
                    greeting = await asyncio.wait_for(generate_greeting(job, resume_text, use_ai=True), timeout=LLM_TIMEOUT_SECONDS)
                except asyncio.TimeoutError:
                    greeting = fallback_greeting(job)

                success = await apply_single_job()
                status = 'success' if success else 'failed'

                if success:
                    success_count += 1
                    user.remaining_quota = max(user.remaining_quota - 1, 0)
                else:
                    failed_count += 1

                add_record(user.id, job, status=status, source='smart_apply', greeting=greeting)

                progress = 0.4 + ((idx + 1) / len(jobs)) * 0.6
                await websocket.send_json(
                    {
                        'stage': 'applying',
                        'current': idx + 1,
                        'total': len(jobs),
                        'progress': progress,
                        'job': job['title'],
                        'company': job['company'],
                        'greeting': greeting,
                        'success': success,
                        'success_count': success_count,
                        'failed_count': failed_count,
                        'remaining_quota': user.remaining_quota,
                    }
                )

                await asyncio.sleep(STEP_DELAY_SECONDS)
            except Exception as exc:
                failed_count += 1
                await websocket.send_json({'stage': 'warning', 'message': f'单条投递异常：{exc}', 'progress': 0.8})

        await websocket.send_json(
            {
                'stage': 'completed',
                'message': f'投递完成！成功 {success_count} 个，失败 {failed_count} 个',
                'progress': 1.0,
                'success_count': success_count,
                'failed_count': failed_count,
                'remaining_quota': user.remaining_quota,
            }
        )

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({'error': True, 'message': f'服务异常: {exc}'})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@app.websocket('/api/apply/ws/apply')
async def websocket_batch_apply(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        data = await websocket.receive_json()

        token = str(data.get('token', ''))
        user_id = verify_token(token)
        user = users_db.get(user_id) if user_id else None

        job_ids = data.get('job_ids') or []
        resume_text = str(data.get('resume_text', ''))
        use_ai = bool(data.get('use_ai_cover_letter', True))

        if not isinstance(job_ids, list) or not job_ids:
            await websocket.send_json({'error': True, 'message': '请选择至少一个岗位'})
            await websocket.close()
            return

        if user and user.remaining_quota <= 0:
            await websocket.send_json({'error': True, 'message': '投递次数已用完，请升级套餐'})
            await websocket.close()
            return

        jobs: List[Dict[str, Any]] = []
        for idx, job_id in enumerate(job_ids):
            cached = job_index.get(job_id)
            if cached:
                jobs.append(cached)
            else:
                jobs.append(
                    {
                        'job_id': job_id,
                        'id': job_id,
                        'title': f'目标岗位 {idx + 1}',
                        'company': f'目标公司 {idx + 1}',
                        'salary': '10-20K',
                        'location': '全国',
                        'experience': '1-3年',
                        'education': '本科及以上',
                        'description': '来自批量投递队列的岗位。',
                    }
                )

        total = len(jobs)
        success_count = 0
        failed_count = 0

        await websocket.send_json({'stage': 'applying', 'message': f'开始处理 {total} 个岗位', 'progress': 0.02})

        for idx, job in enumerate(jobs):
            if user and user.remaining_quota <= 0:
                await websocket.send_json({'error': True, 'message': '额度不足，投递提前结束'})
                break

            try:
                try:
                    greeting = await asyncio.wait_for(generate_greeting(job, resume_text, use_ai=use_ai), timeout=LLM_TIMEOUT_SECONDS)
                except asyncio.TimeoutError:
                    greeting = fallback_greeting(job)

                success = await apply_single_job()
                status = 'success' if success else 'failed'

                if success:
                    success_count += 1
                    if user:
                        user.remaining_quota = max(user.remaining_quota - 1, 0)
                else:
                    failed_count += 1

                if user:
                    add_record(user.id, job, status=status, source='auto_apply', greeting=greeting)

                progress = (idx + 1) / total
                await websocket.send_json(
                    {
                        'current': idx + 1,
                        'total': total,
                        'progress': progress,
                        'job': job.get('title'),
                        'company': job.get('company'),
                        'success': success,
                        'greeting': greeting,
                        'success_count': success_count,
                        'failed_count': failed_count,
                        'remaining_quota': user.remaining_quota if user else None,
                    }
                )

                await asyncio.sleep(STEP_DELAY_SECONDS)
            except Exception as exc:
                failed_count += 1
                await websocket.send_json({'error': True, 'message': f'单条投递异常：{exc}'})

        await websocket.send_json(
            {
                'completed': True,
                'stage': 'completed',
                'message': f'批量投递完成：成功 {success_count} 个，失败 {failed_count} 个',
                'success_count': success_count,
                'failed_count': failed_count,
                'remaining_quota': user.remaining_quota if user else None,
            }
        )

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({'error': True, 'message': f'服务异常: {exc}'})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == '__main__':
    import uvicorn

    print('AI求职助手云端版启动中...')
    print('后端地址: http://0.0.0.0:8765')
    print('API 文档: http://0.0.0.0:8765/docs')
    uvicorn.run(app, host='0.0.0.0', port=8765)
