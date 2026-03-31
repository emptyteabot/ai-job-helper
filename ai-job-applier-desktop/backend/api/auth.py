"""
认证相关 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

# 暂时禁用 playwright 相关导入
# from automation.boss_applier import BossApplier
# from automation.config import AutoApplyConfig

router = APIRouter(prefix="/api/auth", tags=["认证"])
logger = logging.getLogger(__name__)

# 全局 applier 实例
_applier: Optional[any] = None


class LoginRequest(BaseModel):
    phone: str
    headless: bool = False


class LoginResponse(BaseModel):
    success: bool
    message: str
    session_saved: bool = False


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    登录 Boss直聘
    使用手机号验证码登录
    """
    # 暂时返回提示信息
    return LoginResponse(
        success=False,
        message="Boss 自动投递功能正在部署中，请稍后再试"
    )


@router.post("/logout")
async def logout():
    """登出并清理会话"""
    global _applier

    try:
        if _applier:
            await _applier.close()
            _applier = None

        return {"success": True, "message": "登出成功"}
    except Exception as e:
        logger.error(f"登出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """获取登录状态"""
    global _applier

    is_logged_in = _applier is not None and _applier.page is not None

    return {
        "logged_in": is_logged_in,
        "platform": "boss" if is_logged_in else None
    }


def get_applier() -> Optional[any]:
    """获取当前 applier 实例"""
    return _applier
