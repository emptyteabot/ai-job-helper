"""
会话管理器
处理 Cookie 持久化、登录状态保持
"""

import json
import os
import pickle
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """会话管理器"""

    def __init__(self, platform: str, cache_dir: str = ".cache/sessions"):
        """
        初始化会话管理器

        Args:
            platform: 平台名称
            cache_dir: 缓存目录
        """
        self.platform = platform
        self.cache_dir = cache_dir
        self.session_file = os.path.join(cache_dir, f"{platform}_session.pkl")

        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)

    def save_cookies(self, driver, user_id: str = "default"):
        """
        保存浏览器 Cookies

        Args:
            driver: Selenium WebDriver 或 DrissionPage ChromiumPage 实例
            user_id: 用户标识
        """
        try:
            # 检测驱动类型
            driver_type = type(driver).__name__

            if driver_type == 'ChromiumPage':
                # DrissionPage
                cookies = driver.cookies()
                user_agent = driver.user_agent
            else:
                # Selenium
                cookies = driver.get_cookies()
                user_agent = driver.execute_script("return navigator.userAgent")

            session_data = {
                'user_id': user_id,
                'platform': self.platform,
                'cookies': cookies,
                'timestamp': datetime.now().isoformat(),
                'user_agent': user_agent,
                'driver_type': driver_type
            }

            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)

            logger.info(f"Cookies 已保存: {self.session_file}")
            return True

        except Exception as e:
            logger.error(f"保存 Cookies 失败: {e}")
            return False

    def load_cookies(self, driver, user_id: str = "default") -> bool:
        """
        加载 Cookies 到浏览器

        Args:
            driver: Selenium WebDriver 或 DrissionPage ChromiumPage 实例
            user_id: 用户标识

        Returns:
            bool: 是否成功加载
        """
        try:
            if not os.path.exists(self.session_file):
                logger.info("未找到已保存的会话")
                return False

            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)

            # 检查会话是否过期（7天）
            saved_time = datetime.fromisoformat(session_data['timestamp'])
            if datetime.now() - saved_time > timedelta(days=7):
                logger.info("会话已过期")
                return False

            # 检查用户ID是否匹配
            if session_data.get('user_id') != user_id:
                logger.info("用户ID不匹配")
                return False

            # 检测驱动类型
            driver_type = type(driver).__name__
            cookies = session_data['cookies']

            # 加载 Cookies
            if driver_type == 'ChromiumPage':
                # DrissionPage - 使用字典格式
                if isinstance(cookies, dict):
                    # 已经是字典格式
                    for name, value in cookies.items():
                        driver.set.cookies({name: value})
                else:
                    # 列表格式，转换为字典
                    for cookie in cookies:
                        try:
                            if isinstance(cookie, dict):
                                driver.set.cookies(cookie)
                        except Exception as e:
                            logger.warning(f"加载 Cookie 失败: {cookie.get('name', 'unknown')}, 错误: {e}")
            else:
                # Selenium
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"加载 Cookie 失败: {cookie.get('name', 'unknown')}, 错误: {e}")

            logger.info("Cookies 已加载")
            return True

        except Exception as e:
            logger.error(f"加载 Cookies 失败: {e}")
            return False

    def clear_session(self):
        """清除保存的会话"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                logger.info("会话已清除")
                return True
        except Exception as e:
            logger.error(f"清除会话失败: {e}")
            return False

    def is_session_valid(self, user_id: str = "default") -> bool:
        """
        检查会话是否有效

        Args:
            user_id: 用户标识

        Returns:
            bool: 会话是否有效
        """
        try:
            if not os.path.exists(self.session_file):
                return False

            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)

            # 检查过期时间
            saved_time = datetime.fromisoformat(session_data['timestamp'])
            if datetime.now() - saved_time > timedelta(days=7):
                return False

            # 检查用户ID
            if session_data.get('user_id') != user_id:
                return False

            return True

        except Exception as e:
            logger.error(f"检查会话有效性失败: {e}")
            return False

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        try:
            if not os.path.exists(self.session_file):
                return None

            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)

            return {
                'user_id': session_data.get('user_id'),
                'platform': session_data.get('platform'),
                'timestamp': session_data.get('timestamp'),
                'cookie_count': len(session_data.get('cookies', [])),
                'is_valid': self.is_session_valid(session_data.get('user_id', 'default'))
            }

        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return None
