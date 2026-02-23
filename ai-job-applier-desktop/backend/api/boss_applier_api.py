"""
Boss 直聘自动投递 API - 使用高星项目的 BossApplier
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import sys
import os
from pathlib import Path

# 添加自动投简历项目到路径
current_dir = Path(__file__).parent.parent.parent  # backend 的父目录
auto_apply_path = current_dir / "自动投简历"

if auto_apply_path.exists():
    sys.path.insert(0, str(auto_apply_path))
    try:
        from app.services.auto_apply.boss_applier import BossApplier
        logging.info(f"成功加载 BossApplier from {auto_apply_path}")
    except Exception as e:
        BossApplier = None
        logging.error(f"加载 BossApplier 失败: {e}")
else:
    # 如果找不到，使用备用方案
    BossApplier = None
    logging.warning(f"未找到自动投简历项目: {auto_apply_path}")

router = APIRouter(prefix="/api/boss", tags=["Boss直聘"])
logger = logging.getLogger(__name__)

# 全局 BossApplier 实例
_boss_applier: Optional[BossApplier] = None


class LoginRequest(BaseModel):
    phone: str


class SearchRequest(BaseModel):
    keywords: str
    location: str = "北京"
    salary: Optional[str] = None
    experience: Optional[str] = None


class ApplyRequest(BaseModel):
    keywords: str
    location: str = "北京"
    max_count: int = 10
    greeting: str = "您好，我对这个职位很感兴趣，期待与您沟通。"
    filters: dict = {}


def get_boss_applier() -> BossApplier:
    """获取 BossApplier 实例"""
    global _boss_applier
    
    if BossApplier is None:
        raise HTTPException(
            status_code=500,
            detail="BossApplier 未安装，请检查自动投简历项目是否存在"
        )
    
    if _boss_applier is None:
        config = {
            'headless': False,  # 显示浏览器
            'random_delay_min': 2,
            'random_delay_max': 5,
            'company_blacklist': ['外包', '劳务派遣', '猎头'],
            'title_blacklist': ['实习', '兼职'],
            'greeting': '您好，我对这个职位很感兴趣，期待与您沟通。'
        }
        _boss_applier = BossApplier(config)
    return _boss_applier


@router.post("/login")
async def login(request: LoginRequest):
    """
    登录 Boss 直聘
    
    需要在浏览器中手动输入验证码
    """
    try:
        applier = get_boss_applier()
        success = applier.login(request.phone)
        
        if success:
            return {"success": True, "message": "登录成功"}
        else:
            raise HTTPException(status_code=401, detail="登录失败")
    
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_jobs(request: SearchRequest):
    """
    搜索职位
    """
    try:
        applier = get_boss_applier()
        
        filters = {}
        if request.salary:
            filters['salary'] = request.salary
        if request.experience:
            filters['experience'] = request.experience
        
        jobs = applier.search_jobs(
            keywords=request.keywords,
            location=request.location,
            filters=filters
        )
        
        return {
            "success": True,
            "count": len(jobs),
            "jobs": jobs
        }
    
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply")
async def auto_apply(request: ApplyRequest):
    """
    自动投递
    
    1. 搜索职位
    2. 批量投递
    3. 返回结果
    """
    try:
        applier = get_boss_applier()
        
        # 更新配置
        if request.greeting:
            applier.config['greeting'] = request.greeting
        
        # 搜索职位
        logger.info(f"搜索职位: {request.keywords} @ {request.location}")
        jobs = applier.search_jobs(
            keywords=request.keywords,
            location=request.location,
            filters=request.filters
        )
        
        if not jobs:
            return {
                "success": False,
                "message": "未找到符合条件的职位"
            }
        
        # 限制投递数量
        jobs = jobs[:request.max_count]
        
        # 批量投递
        logger.info(f"开始投递 {len(jobs)} 个职位")
        results = []
        success_count = 0
        failed_count = 0
        
        for job in jobs:
            result = applier.apply_job(job)
            results.append(result)
            
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            "success": True,
            "message": f"投递完成: 成功 {success_count}, 失败 {failed_count}",
            "total": len(jobs),
            "success_count": success_count,
            "failed_count": failed_count,
            "details": results
        }
    
    except Exception as e:
        logger.error(f"自动投递失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup():
    """
    清理资源（关闭浏览器）
    """
    try:
        global _boss_applier
        if _boss_applier:
            _boss_applier.cleanup()
            _boss_applier = None
        
        return {"success": True, "message": "资源已清理"}
    
    except Exception as e:
        logger.error(f"清理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

