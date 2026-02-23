"""
多用户 Session 管理器
每个用户独立的 BossApplier 实例
"""
import uuid
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class UserSession:
    """用户会话"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.boss_applier = None
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.is_logged_in = False
        
    def update_activity(self):
        """更新活跃时间"""
        self.last_active = datetime.now()
    
    def is_expired(self, timeout_hours: int = 24) -> bool:
        """检查是否过期"""
        return datetime.now() - self.last_active > timedelta(hours=timeout_hours)


class MultiUserSessionManager:
    """多用户会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self._cleanup_task = None
        
    def create_session(self) -> str:
        """创建新会话"""
        user_id = str(uuid.uuid4())
        session = UserSession(user_id)
        self.sessions[user_id] = session
        logger.info(f"创建新会话: {user_id}")
        return user_id
    
    def get_session(self, user_id: str) -> Optional[UserSession]:
        """获取会话"""
        session = self.sessions.get(user_id)
        if session:
            session.update_activity()
        return session
    
    def remove_session(self, user_id: str):
        """移除会话"""
        if user_id in self.sessions:
            session = self.sessions[user_id]
            if session.boss_applier:
                try:
                    session.boss_applier.cleanup()
                except:
                    pass
            del self.sessions[user_id]
            logger.info(f"移除会话: {user_id}")
    
    async def cleanup_expired_sessions(self):
        """清理过期会话"""
        while True:
            try:
                expired_users = [
                    user_id for user_id, session in self.sessions.items()
                    if session.is_expired()
                ]
                
                for user_id in expired_users:
                    logger.info(f"清理过期会话: {user_id}")
                    self.remove_session(user_id)
                
                # 每小时检查一次
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"清理会话失败: {e}")
                await asyncio.sleep(60)
    
    def start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self.cleanup_expired_sessions())
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": sum(1 for s in self.sessions.values() if not s.is_expired()),
            "logged_in_sessions": sum(1 for s in self.sessions.values() if s.is_logged_in)
        }


# 全局实例
_session_manager = MultiUserSessionManager()


def get_session_manager() -> MultiUserSessionManager:
    """获取会话管理器"""
    return _session_manager

