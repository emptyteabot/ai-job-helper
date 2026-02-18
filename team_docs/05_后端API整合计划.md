# 后端 API 整合计划

## 1. API 清单

### 1.1 核心业务 API

#### 简历处理
- `POST /api/upload` - 上传简历文件（PDF/Word/图片/TXT）
- `POST /api/process` - 处理简历，执行 AI 分析流程
- `WS /ws/progress` - 实时进度推送（WebSocket）

#### 岗位搜索
- `GET /api/jobs/search` - 搜索真实岗位
  - 参数：keywords, location, salary_min, experience, limit
  - 支持多数据源：云端缓存、OpenClaw、搜索引擎、企业 API
- `GET /api/jobs/{job_id}` - 获取单个岗位详情
- `POST /api/jobs/apply` - 单个岗位投递
- `POST /api/jobs/batch_apply` - 批量投递

#### 自动投递
- `POST /api/auto-apply/start` - 启动自动投递任务
- `POST /api/auto-apply/start-multi` - 多平台自动投递
- `POST /api/auto-apply/stop` - 停止投递任务
- `GET /api/auto-apply/status/{task_id}` - 查询任务状态
- `GET /api/auto-apply/history` - 投递历史记录
- `GET /api/auto-apply/platforms` - 获取支持的平台列表
- `GET /api/auto-apply/stats` - 投递统计数据
- `POST /api/auto-apply/test-platform` - 测试平台连接
- `WS /ws/auto-apply/{task_id}` - 投递进度实时推送

### 1.2 系统监控 API

#### 健康检查
- `GET /api/health` - 系统健康状态
- `GET /api/ready` - 就绪检查
- `GET /api/ping` - 心跳检测
- `GET /api/version` - 版本信息

#### 业务指标
- `GET /api/business/metrics` - 业务指标统计
- `GET /api/business/readiness` - 业务就绪度
- `GET /api/statistics` - 系统统计数据

### 1.3 数据采集 API

#### 爬虫服务
- `POST /api/crawler/upload` - 上传爬虫采集的岗位数据
- `GET /api/crawler/status` - 爬虫状态和云端缓存信息

#### 用户反馈
- `POST /api/business/lead` - 提交潜在客户信息
- `POST /api/business/feedback` - 提交用户反馈
- `POST /api/business/event` - 记录业务事件
- `GET /api/business/feedback/summary` - 反馈汇总

### 1.4 投资人 API
- `GET /api/investor/readiness` - 融资就绪度评估
- `GET /api/investor/summary` - 投资人数据摘要
- `GET /investor` - 投资人仪表板页面

---

## 2. Streamlit 与 FastAPI 整合方案

### 2.1 架构设计

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit 前端                      │
│  (streamlit_app.py + pages/*.py)                    │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/WebSocket
                   ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI 后端服务                        │
│                (web_app.py)                         │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  简历处理    │  │  岗位搜索    │  │ 自动投递  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  AI 引擎     │  │  数据采集    │  │ 监控统计  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              核心服务层                              │
├─────────────────────────────────────────────────────┤
│  • ResumeAnalyzer (简历分析)                        │
│  • JobSearcher (岗位搜索)                           │
│  • RealJobService (真实岗位服务)                    │
│  • AgentOrchestrator (AI 协调器)                    │
│  • BaseApplier (投递基类)                           │
│    - LinkedInApplier                                │
│    - BossApplier                                    │
│    - ZhilianApplier                                 │
└─────────────────────────────────────────────────────┘
```

### 2.2 整合策略

#### 方案 A：独立部署（推荐）
- **FastAPI**：独立运行在 8000 端口
- **Streamlit**：独立运行在 8501 端口
- **通信**：Streamlit 通过 HTTP 调用 FastAPI
- **优点**：解耦、易扩展、可独立升级
- **缺点**：需要管理两个进程

#### 方案 B：嵌入式部署
- **FastAPI** 作为主服务
- **Streamlit** 通过 iframe 嵌入或反向代理
- **优点**：单一入口、部署简单
- **缺点**：耦合度高、Streamlit 限制多

#### 方案 C：混合部署（当前状态）
- **FastAPI** 提供 API 和 Web 界面
- **Streamlit** 作为独立的管理界面
- **优点**：灵活、各司其职
- **缺点**：用户需要访问两个地址

**推荐：方案 A（独立部署）**

---

## 3. 数据流设计

### 3.1 简历分析流程

```
用户上传简历
    ↓
Streamlit: st.file_uploader()
    ↓
POST /api/upload (FastAPI)
    ↓
文件解析 (PDF/Word/图片 OCR)
    ↓
ResumeAnalyzer.extract_info()
    ↓
返回简历信息 JSON
    ↓
Streamlit 展示结果
```

### 3.2 AI 处理流程

```
用户点击"开始分析"
    ↓
Streamlit: st.button()
    ↓
POST /api/process (FastAPI)
    ↓
market_driven_pipeline.process_resume()
    ↓
AgentOrchestrator 协调 6 个 AI Agent
    ├─ PLANNER (职业规划)
    ├─ RECRUITER (岗位推荐)
    ├─ OPTIMIZER (简历优化)
    ├─ REVIEWER (质量审核)
    ├─ COACH (面试辅导)
    └─ INTERVIEWER (模拟面试)
    ↓
实时进度推送 (WebSocket)
    ↓
Streamlit 通过 st.empty() 更新进度
    ↓
返回完整分析结果
```

### 3.3 岗位搜索流程

```
用户输入搜索条件
    ↓
Streamlit: st.text_input(), st.multiselect()
    ↓
GET /api/jobs/search?keywords=xxx&location=xxx
    ↓
RealJobService.search_jobs()
    ↓
数据源优先级：
    1. 云端缓存 (cloud_jobs_cache)
    2. OpenClaw 实时爬取
    3. 搜索引擎 (Baidu/Bing/Brave)
    4. 企业 API
    5. Jooble API
    ↓
_normalize_real_jobs() 数据标准化
    ↓
_enforce_cn_market_jobs() 过滤非中国岗位
    ↓
返回岗位列表 JSON
    ↓
Streamlit 展示岗位卡片
```

### 3.4 自动投递流程

```
用户配置投递参数
    ↓
Streamlit: 平台选择、数量、间隔
    ↓
POST /api/auto-apply/start
    ↓
创建任务 (task_id)
    ↓
异步执行 _run_auto_apply_task()
    ├─ 初始化 Applier (LinkedIn/Boss/Zhilian)
    ├─ 登录平台
    ├─ 搜索岗位
    ├─ 批量投递 batch_apply()
    └─ 更新任务状态
    ↓
WebSocket 实时推送进度
    ↓
Streamlit 展示投递进度和结果
```

---

## 4. API 调用策略

### 4.1 Streamlit 调用 FastAPI

#### 方法 1：使用 requests 库
```python
import requests
import streamlit as st

API_BASE = "http://localhost:8000"

def upload_resume(file):
    files = {"file": file}
    response = requests.post(f"{API_BASE}/api/upload", files=files)
    return response.json()

def process_resume(resume_text):
    data = {"resume": resume_text}
    response = requests.post(f"{API_BASE}/api/process", json=data)
    return response.json()

def search_jobs(keywords, location):
    params = {"keywords": keywords, "location": location}
    response = requests.get(f"{API_BASE}/api/jobs/search", params=params)
    return response.json()
```

#### 方法 2：使用 httpx（异步）
```python
import httpx
import asyncio

async def async_process_resume(resume_text):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/process",
            json={"resume": resume_text}
        )
        return response.json()

# Streamlit 中调用
result = asyncio.run(async_process_resume(resume_text))
```

#### 方法 3：WebSocket 实时通信
```python
import websocket
import json
import threading

def on_message(ws, message):
    data = json.loads(message)
    st.session_state.progress = data

def connect_websocket():
    ws = websocket.WebSocketApp(
        "ws://localhost:8000/ws/progress",
        on_message=on_message
    )
    thread = threading.Thread(target=ws.run_forever)
    thread.daemon = True
    thread.start()
```

### 4.2 错误处理

```python
def safe_api_call(func, *args, **kwargs):
    try:
        response = func(*args, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 错误: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("无法连接到后端服务，请检查 FastAPI 是否运行")
        return None
    except Exception as e:
        st.error(f"请求失败: {str(e)}")
        return None
```

### 4.3 缓存策略

```python
@st.cache_data(ttl=300)  # 缓存 5 分钟
def cached_search_jobs(keywords, location):
    return search_jobs(keywords, location)

@st.cache_resource
def get_api_client():
    return httpx.Client(base_url=API_BASE)
```

---

## 5. 错误处理

### 5.1 API 层错误处理

#### FastAPI 统一错误响应
```python
def _api_error(message: str, status_code: int = 400, code: str = "bad_request"):
    return JSONResponse(
        {"success": False, "error": message, "code": code},
        status_code=status_code,
    )

# 使用示例
if not resume_text:
    return _api_error("简历内容不能为空", 400, "empty_resume")
```

#### 中间件错误捕获
```python
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception("请求失败")
        return JSONResponse(
            {"success": False, "error": "internal_error"},
            status_code=500
        )
    return response
```

### 5.2 服务层错误处理

#### 重试机制
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def search_jobs_with_retry(keywords, location):
    return real_job_service.search_jobs(keywords, location)
```

#### 降级策略
```python
def search_jobs_with_fallback(keywords, location):
    try:
        # 优先使用 OpenClaw
        return openclaw_provider.search(keywords, location)
    except Exception as e:
        logger.warning(f"OpenClaw 失败: {e}")
        try:
            # 降级到搜索引擎
            return bing_provider.search(keywords, location)
        except Exception as e2:
            logger.warning(f"Bing 失败: {e2}")
            # 最后使用云端缓存
            return _filter_cloud_cache_by_query(keywords, location)
```

### 5.3 Streamlit 层错误处理

```python
def handle_api_response(response):
    if response is None:
        st.error("API 调用失败")
        return None

    if not response.get("success", False):
        error_msg = response.get("error", "未知错误")
        error_code = response.get("code", "unknown")
        st.error(f"错误 [{error_code}]: {error_msg}")
        return None

    return response

# 使用示例
response = safe_api_call(requests.post, f"{API_BASE}/api/process", json=data)
result = handle_api_response(response)
if result:
    st.success("处理成功")
```

---

## 6. 性能优化

### 6.1 API 性能优化

#### 异步处理
```python
@app.post("/api/process")
async def process_resume(request: Request):
    data = await request.json()
    # 异步处理，不阻塞
    results = await market_engine.process_resume(data["resume"])
    return _api_success(results)
```

#### 后台任务
```python
from fastapi import BackgroundTasks

@app.post("/api/auto-apply/start")
async def start_auto_apply(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    task_id = str(uuid.uuid4())

    # 后台执行，立即返回
    background_tasks.add_task(_run_auto_apply_task, task_id, data)

    return _api_success({"task_id": task_id})
```

#### 响应压缩
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 6.2 数据缓存

#### 内存缓存
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_job_details(job_id: str):
    return real_job_service.get_job(job_id)
```

#### Redis 缓存
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_jobs(key: str, jobs: List[Dict], ttl: int = 300):
    redis_client.setex(key, ttl, json.dumps(jobs))

def get_cached_jobs(key: str):
    data = redis_client.get(key)
    return json.loads(data) if data else None
```

### 6.3 数据库优化

#### 批量插入
```python
def batch_save_jobs(jobs: List[Dict]):
    # 使用批量插入而非逐条插入
    db.bulk_insert_mappings(Job, jobs)
    db.commit()
```

#### 索引优化
```python
# 为常用查询字段添加索引
class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    title = Column(String, index=True)  # 添加索引
    location = Column(String, index=True)
    created_at = Column(DateTime, index=True)
```

### 6.4 前端优化

#### Streamlit 缓存
```python
@st.cache_data(ttl=600)
def load_jobs(keywords, location):
    return search_jobs(keywords, location)

@st.cache_resource
def init_api_client():
    return APIClient(base_url=API_BASE)
```

#### 分页加载
```python
def display_jobs_paginated(jobs, page_size=10):
    total_pages = (len(jobs) - 1) // page_size + 1
    page = st.number_input("页码", 1, total_pages, 1)

    start = (page - 1) * page_size
    end = start + page_size

    for job in jobs[start:end]:
        display_job_card(job)
```

---

## 7. 开发计划

### 7.1 第一阶段：API 封装（1-2 天）

**目标**：创建统一的 API 客户端

**任务**：
1. 创建 `api_client.py` 封装所有 API 调用
2. 实现错误处理和重试机制
3. 添加日志记录
4. 编写单元测试

**交付物**：
- `app/client/api_client.py`
- `tests/test_api_client.py`

### 7.2 第二阶段：Streamlit 重构（2-3 天）

**目标**：将 Streamlit 改为纯前端，调用 FastAPI

**任务**：
1. 重构 `streamlit_app.py`，移除业务逻辑
2. 使用 `api_client` 替换直接调用服务
3. 实现 WebSocket 实时更新
4. 优化 UI 交互

**交付物**：
- 重构后的 `streamlit_app.py`
- 更新的 `pages/*.py`

### 7.3 第三阶段：性能优化（1-2 天）

**目标**：提升系统性能和稳定性

**任务**：
1. 添加缓存机制（Redis）
2. 实现异步处理
3. 优化数据库查询
4. 添加监控指标

**交付物**：
- 性能测试报告
- 优化后的代码

### 7.4 第四阶段：部署和测试（1 天）

**目标**：完成整合和部署

**任务**：
1. 编写 Docker Compose 配置
2. 配置 Nginx 反向代理
3. 端到端测试
4. 编写部署文档

**交付物**：
- `docker-compose.yml`
- `nginx.conf`
- 部署文档

---

## 8. 技术栈

### 8.1 后端
- **FastAPI** 0.104+ - Web 框架
- **Uvicorn** - ASGI 服务器
- **Pydantic** - 数据验证
- **SQLAlchemy** - ORM（可选）
- **Redis** - 缓存（可选）

### 8.2 前端
- **Streamlit** 1.28+ - Web UI
- **requests** / **httpx** - HTTP 客户端
- **websocket-client** - WebSocket 客户端

### 8.3 AI 引擎
- **OpenAI API** / **Gemini API** - LLM
- **LangChain** - AI 编排（可选）

### 8.4 爬虫
- **Selenium** - 浏览器自动化
- **BeautifulSoup** - HTML 解析
- **OpenClaw** - 智能爬虫框架

---

## 9. 部署架构

### 9.1 开发环境

```
┌─────────────────────────────────────┐
│  开发机器 (localhost)                │
├─────────────────────────────────────┤
│  FastAPI:  http://localhost:8000    │
│  Streamlit: http://localhost:8501   │
└─────────────────────────────────────┘
```

### 9.2 生产环境（Docker）

```
┌─────────────────────────────────────────────────┐
│              Nginx (80/443)                     │
│  - /api/* → FastAPI                             │
│  - /* → Streamlit                               │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌─────────┐         ┌─────────┐
│ FastAPI │         │Streamlit│
│  :8000  │         │  :8501  │
└────┬────┘         └─────────┘
     │
     ▼
┌─────────┐
│  Redis  │
│  :6379  │
└─────────┘
```

### 9.3 Docker Compose 配置

```yaml
version: '3.8'

services:
  fastapi:
    build: .
    command: uvicorn web_app:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  streamlit:
    build: .
    command: streamlit run streamlit_app.py --server.port 8501
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://fastapi:8000

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - fastapi
      - streamlit
```

---

## 10. 监控和日志

### 10.1 日志策略

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用日志
logger.info("API 调用成功")
logger.error("处理失败", exc_info=True)
```

### 10.2 性能监控

```python
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.url.path} took {process_time:.2f}s")
    return response
```

### 10.3 健康检查

```python
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": check_redis_connection(),
            "database": check_db_connection(),
            "ai_engine": check_ai_engine()
        }
    }
```

---

## 11. 安全考虑

### 11.1 API 认证

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.post("/api/process", dependencies=[Depends(verify_api_key)])
async def process_resume(request: Request):
    # 受保护的端点
    pass
```

### 11.2 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/process")
@limiter.limit("10/minute")
async def process_resume(request: Request):
    pass
```

### 11.3 输入验证

```python
from pydantic import BaseModel, validator

class ResumeRequest(BaseModel):
    resume: str

    @validator('resume')
    def validate_resume(cls, v):
        if len(v) < 100:
            raise ValueError('简历内容过短')
        if len(v) > 50000:
            raise ValueError('简历内容过长')
        return v
```

---

## 12. 总结

### 核心要点
1. **解耦设计**：Streamlit 作为纯前端，FastAPI 作为后端服务
2. **统一 API**：所有业务逻辑通过 RESTful API 暴露
3. **实时通信**：使用 WebSocket 推送进度和状态
4. **错误处理**：多层错误处理和降级策略
5. **性能优化**：缓存、异步、批量处理

### 下一步行动
1. 创建 `api_client.py` 封装 API 调用
2. 重构 Streamlit 代码，移除直接服务调用
3. 实现 WebSocket 实时更新
4. 添加缓存和性能优化
5. 编写测试和部署文档

### 预期收益
- **可维护性**：前后端分离，职责清晰
- **可扩展性**：API 可被其他客户端调用
- **性能**：缓存和异步处理提升响应速度
- **稳定性**：错误处理和降级策略提高可用性
