"""
无脑自动投递 API
用户提供手机号 → 登录自己的 Boss 账号 → 自动投递
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict
import logging
import asyncio
from datetime import datetime
import sys
from pathlib import Path
import urllib.parse
import random

# 添加自动投简历项目到路径
current_dir = Path(__file__).parent.parent.parent
auto_apply_path = current_dir / "自动投简历"

if auto_apply_path.exists():
    sys.path.insert(0, str(auto_apply_path))
    try:
        from app.services.auto_apply.boss_applier import BossApplier
        logger = logging.getLogger(__name__)
        logger.info(f"成功加载 BossApplier from {auto_apply_path}")
    except Exception as e:
        BossApplier = None
        logger = logging.getLogger(__name__)
        logger.error(f"加载 BossApplier 失败: {e}")
else:
    BossApplier = None
    logger = logging.getLogger(__name__)
    logger.warning(f"未找到自动投简历项目: {auto_apply_path}")

router = APIRouter(prefix="/api/simple-apply", tags=["无脑投递"])

# Boss 直聘城市代码
CITY_CODES = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280100",
    "深圳": "101280600",
    "杭州": "101210100",
    "成都": "101270100",
    "南京": "101190100",
    "武汉": "101200100",
    "西安": "101110100",
    "重庆": "101040100",
    "苏州": "101190400",
    "天津": "101030100",
    "郑州": "101180100",
    "长沙": "101250100",
}

def get_city_code(city_name: str) -> str:
    """获取城市代码"""
    city_name = city_name.replace("市", "")
    return CITY_CODES.get(city_name, CITY_CODES["北京"])


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str  # 手机号


class VerifyCodeRequest(BaseModel):
    """验证码请求"""
    phone: str
    code: str


class ApplyRequest(BaseModel):
    """投递请求"""
    phone: str  # 手机号（用于识别用户）
    resume_text: str  # 简历文本
    job_keyword: str  # 岗位关键词
    city: str  # 城市
    count: int = 10  # 投递数量
    email: Optional[str] = None  # 通知邮箱


# 用户 Session 管理
_user_sessions: Dict[str, BossApplier] = {}


def get_user_applier(phone: str) -> Optional[BossApplier]:
    """获取用户的 BossApplier 实例"""
    return _user_sessions.get(phone)


def create_user_applier(phone: str) -> BossApplier:
    """创建用户的 BossApplier 实例"""
    if BossApplier is None:
        raise HTTPException(status_code=500, detail="BossApplier 未安装")
    
    config = {
        'headless': False,  # 显示浏览器（方便用户看到登录过程）
        'random_delay_min': 2,
        'random_delay_max': 5,
        'company_blacklist': ['外包', '劳务派遣', '猎头'],
        'title_blacklist': [],
        'greeting': '您好，我对这个职位很感兴趣，期待与您沟通。'
    }
    
    applier = BossApplier(config)
    _user_sessions[phone] = applier
    return applier


@router.post("/init-login")
async def init_login(request: LoginRequest):
    """
    步骤1：初始化登录 - 打开浏览器并自动填写手机号、获取验证码
    
    流程：
    1. 后端启动浏览器（保持打开）
    2. 自动访问登录页
    3. 自动填写手机号
    4. 自动点击"获取验证码"
    5. 返回成功，等待用户输入验证码
    """
    try:
        if not request.phone or len(request.phone) != 11:
            raise HTTPException(status_code=400, detail="请输入正确的手机号")
        
        # 检查是否已登录
        applier = get_user_applier(request.phone)
        if applier and hasattr(applier, 'page') and applier.page:
            # 检查是否真的登录了
            try:
                current_url = applier.page.url
                if 'zhipin.com' in current_url and 'login' not in current_url:
                    return {
                        "success": True,
                        "message": "已登录，无需重复登录",
                        "phone": request.phone,
                        "step": "completed"
                    }
            except:
                pass
        
        # 创建新的 BossApplier
        applier = create_user_applier(request.phone)
        
        logger.info(f"用户 {request.phone} 开始初始化登录...")
        
        # 初始化浏览器
        if not await applier._init_browser():
            raise HTTPException(status_code=500, detail="浏览器初始化失败")
        
        # 访问登录页
        logger.info("正在访问登录页...")
        await applier.page.goto(applier.login_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # 点击手机号登录
        try:
            phone_tab = await applier.page.wait_for_selector('text=手机号登录', timeout=5000)
            await phone_tab.click()
            await asyncio.sleep(1)
        except:
            logger.info("已在手机号登录页面")
        
        # 自动输入手机号
        logger.info("自动输入手机号...")
        phone_input = await applier.page.wait_for_selector('input[placeholder*="手机号"]', timeout=5000)
        await phone_input.click()
        await asyncio.sleep(0.5)
        
        # 逐个字符输入（模拟人类）
        for char in request.phone:
            await phone_input.type(char, delay=random.randint(100, 300))
        
        await asyncio.sleep(1)
        
        # 自动点击获取验证码
        logger.info("自动点击获取验证码...")
        code_button = await applier.page.wait_for_selector('button:has-text("获取验证码")', timeout=5000)
        await code_button.click()
        
        # 处理滑块验证码（如果有）
        try:
            await applier._handle_slider_captcha()
        except:
            pass
        
        await asyncio.sleep(2)
        
        logger.info(f"验证码已发送到 {request.phone}，等待用户输入验证码")
        
        return {
            "success": True,
            "message": f"验证码已发送到 {request.phone}，请输入收到的验证码",
            "phone": request.phone,
            "step": "waiting_code"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化登录失败: {e}", exc_info=True)
        # 清理失败的 session
        if request.phone in _user_sessions:
            try:
                _user_sessions[request.phone].cleanup()
            except:
                pass
            del _user_sessions[request.phone]
        raise HTTPException(status_code=500, detail=f"初始化登录失败: {str(e)}")


class VerifyCodeRequest(BaseModel):
    """验证码请求"""
    phone: str
    code: str


@router.post("/verify-code")
async def verify_code(request: VerifyCodeRequest):
    """
    步骤2：提交验证码完成登录
    
    流程：
    1. 获取用户的浏览器实例
    2. 自动填写验证码
    3. 自动点击登录
    4. 等待登录成功
    """
    try:
        if not request.code or len(request.code) != 6:
            raise HTTPException(status_code=400, detail="请输入6位验证码")
        
        # 获取用户的 BossApplier
        applier = get_user_applier(request.phone)
        if not applier or not applier.page:
            raise HTTPException(status_code=400, detail="请先调用 /init-login 接口")
        
        logger.info(f"用户 {request.phone} 提交验证码...")
        
        # 自动输入验证码
        code_input = await applier.page.wait_for_selector('input[placeholder*="验证码"]', timeout=5000)
        await code_input.click()
        await asyncio.sleep(0.3)
        
        # 逐个字符输入验证码
        for char in request.code:
            await code_input.type(char, delay=random.randint(100, 200))
        
        await asyncio.sleep(1)
        
        # 点击登录按钮
        login_button = await applier.page.wait_for_selector('button:has-text("登录")', timeout=5000)
        await login_button.click()
        
        # 等待登录成功（检测 URL 变化）
        try:
            await applier.page.wait_for_url(f"{applier.base_url}/**", timeout=30000)
            logger.info(f"用户 {request.phone} 登录成功！")
            
            # 保存 Cookies
            try:
                await applier._save_cookies()
            except:
                pass
            
            return {
                "success": True,
                "message": "登录成功！现在可以开始投递了",
                "phone": request.phone
            }
        
        except Exception as e:
            logger.error(f"登录超时: {e}")
            raise HTTPException(status_code=401, detail="登录失败，验证码可能错误或已过期")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证码提交失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证码提交失败: {str(e)}")


@router.post("/apply")
async def auto_apply(request: ApplyRequest):
    """
    自动投递
    
    前提：用户已经登录（调用过 /login 接口）
    """
    try:
        # 验证输入
        if not request.resume_text or len(request.resume_text) < 50:
            raise HTTPException(status_code=400, detail="简历内容太短")
        
        if not request.job_keyword or not request.city:
            raise HTTPException(status_code=400, detail="请填写岗位关键词和城市")
        
        # 获取用户的 BossApplier
        applier = get_user_applier(request.phone)
        if not applier:
            raise HTTPException(
                status_code=401,
                detail="请先登录 Boss 直聘（调用 /login 接口）"
            )
        
        logger.info(f"用户 {request.phone} 开始投递: {request.job_keyword} @ {request.city}")
        
        # 🔥 修复：使用正确的搜索 URL 格式
        # Boss 直聘搜索 URL: https://www.zhipin.com/web/geek/job?query=关键词&city=城市代码
        city_code = get_city_code(request.city)
        
        # URL 编码关键词
        encoded_keyword = urllib.parse.quote(request.job_keyword)
        search_url = f"https://www.zhipin.com/web/geek/job?query={encoded_keyword}&city={city_code}"
        
        logger.info(f"搜索 URL: {search_url}")
        
        # 直接访问搜索页面
        await applier.page.goto(search_url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # 解析职位列表
        jobs = await applier._parse_job_list()
        
        if not jobs:
            return {
                "success": False,
                "message": f"未找到符合条件的岗位。搜索：{request.job_keyword} @ {request.city}",
                "total": 0,
                "success_count": 0,
                "failed_count": 0
            }
        
        # 限制投递数量
        jobs = jobs[:request.count]
        
        logger.info(f"找到 {len(jobs)} 个岗位，开始投递...")
        
        # 批量投递
        results = []
        success_count = 0
        failed_count = 0
        
        for i, job in enumerate(jobs):
            try:
                logger.info(f"投递 {i+1}/{len(jobs)}: {job['title']} @ {job['company']}")
                
                # 🔥 关键修复：直接调用异步方法
                result = await applier._async_apply_job(job)
                results.append(result)
                
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
                
                # 延迟（避免被限流）
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"投递失败: {e}")
                failed_count += 1
        
        logger.info(f"投递完成: 成功 {success_count}, 失败 {failed_count}")
        
        return {
            "success": True,
            "message": f"投递完成！成功 {success_count} 个，失败 {failed_count} 个",
            "total": len(jobs),
            "success_count": success_count,
            "failed_count": failed_count,
            "details": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"自动投递失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{phone}")
async def check_login_status(phone: str):
    """检查用户是否已登录"""
    applier = get_user_applier(phone)
    
    if applier:
        return {
            "logged_in": True,
            "phone": phone,
            "message": "已登录"
        }
    else:
        return {
            "logged_in": False,
            "phone": phone,
            "message": "未登录"
        }


@router.post("/logout/{phone}")
async def logout(phone: str):
    """登出（清理 Session）"""
    applier = get_user_applier(phone)
    
    if applier:
        try:
            applier.cleanup()
        except:
            pass
        
        del _user_sessions[phone]
        
        return {
            "success": True,
            "message": "已登出"
        }
    else:
        return {
            "success": False,
            "message": "未登录"
        }


