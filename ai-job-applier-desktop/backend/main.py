from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import argparse
import logging
from dotenv import load_dotenv

# 导入所有 API 路由
from api import (
    auth,
    jobs,
    apply,
    records,
    resume,
    analysis,
    openclaw,
    smart_apply,
    feishu,
    boss_applier_api,
    simple_apply
)

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="AI Job Applier Desktop Backend",
    version="2.0.0",
    description="AI 求职助手桌面版后端 API - 集成所有功能"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(apply.router)
app.include_router(records.router)
app.include_router(resume.router)
app.include_router(analysis.router)
app.include_router(openclaw.router)
app.include_router(smart_apply.router)
app.include_router(feishu.router)
app.include_router(boss_applier_api.router)
app.include_router(simple_apply.router)

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "AI Job Applier Desktop Backend",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Boss直聘自动投递",
            "简历分析（4个AI Agent）",
            "简历优化",
            "OpenClaw 真实岗位搜索",
            "智能投递",
            "飞书通知",
            "投递记录管理"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "Backend is running"}

@app.get("/api/features")
async def get_features():
    """获取功能列表"""
    return {
        "authentication": "Boss直聘登录",
        "resume_analysis": "简历分析（职业分析、岗位推荐、面试辅导、质量审核）",
        "resume_optimization": "简历优化",
        "job_search": "岗位搜索（Boss直聘 + OpenClaw）",
        "auto_apply": "自动投递",
        "smart_apply": "智能投递",
        "feishu_notification": "飞书通知",
        "application_records": "投递记录管理"
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    uvicorn.run(app, host="127.0.0.1", port=args.port)
