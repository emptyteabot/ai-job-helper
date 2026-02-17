"""
基础投递类
定义所有投递平台的通用接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseApplier(ABC):
    """基础投递类，所有平台投递器的父类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化投递器

        Args:
            config: 配置字典，包含平台特定配置
        """
        self.config = config
        self.driver = None
        self.is_running = False
        self.applied_count = 0
        self.failed_count = 0
        self.history = []

    @abstractmethod
    def login(self, email: str, password: str) -> bool:
        """
        登录平台

        Args:
            email: 用户邮箱
            password: 用户密码

        Returns:
            bool: 登录是否成功
        """
        pass

    @abstractmethod
    def search_jobs(self, keywords: str, location: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        搜索职位

        Args:
            keywords: 搜索关键词
            location: 工作地点
            filters: 其他筛选条件

        Returns:
            List[Dict]: 职位列表
        """
        pass

    @abstractmethod
    def apply_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        申请单个职位

        Args:
            job: 职位信息字典

        Returns:
            Dict: 申请结果 {'success': bool, 'message': str, 'job': dict}
        """
        pass

    def batch_apply(self, jobs: List[Dict[str, Any]], max_count: int = 50) -> Dict[str, Any]:
        """
        批量申请职位

        Args:
            jobs: 职位列表
            max_count: 最大申请数量

        Returns:
            Dict: 批量申请结果统计
        """
        self.is_running = True
        self.applied_count = 0
        self.failed_count = 0
        results = []

        logger.info(f"开始批量投递，目标数量: {max_count}")

        for i, job in enumerate(jobs):
            if not self.is_running:
                logger.info("投递已停止")
                break

            if self.applied_count >= max_count:
                logger.info(f"已达到最大投递数量: {max_count}")
                break

            try:
                logger.info(f"正在投递 [{i+1}/{len(jobs)}]: {job.get('title', 'Unknown')}")
                result = self.apply_job(job)

                if result['success']:
                    self.applied_count += 1
                    logger.info(f"✓ 投递成功: {job.get('title', 'Unknown')}")
                else:
                    self.failed_count += 1
                    logger.warning(f"✗ 投递失败: {job.get('title', 'Unknown')}, 原因: {result.get('message', 'Unknown')}")

                results.append(result)
                self._save_history(result)

            except Exception as e:
                self.failed_count += 1
                error_result = {
                    'success': False,
                    'message': str(e),
                    'job': job,
                    'timestamp': datetime.now().isoformat()
                }
                results.append(error_result)
                self._save_history(error_result)
                logger.exception(f"投递异常: {job.get('title', 'Unknown')}")

        summary = {
            'total_attempted': len(results),
            'applied': self.applied_count,
            'failed': self.failed_count,
            'success_rate': self.applied_count / len(results) if results else 0,
            'results': results
        }

        logger.info(f"批量投递完成: 成功 {self.applied_count}, 失败 {self.failed_count}")
        return summary

    def stop(self):
        """停止投递"""
        self.is_running = False
        logger.info("投递停止指令已发送")

    def _save_history(self, result: Dict[str, Any]):
        """保存投递历史"""
        self.history.append(result)

    def get_history(self) -> List[Dict[str, Any]]:
        """获取投递历史"""
        return self.history

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'is_running': self.is_running,
            'applied_count': self.applied_count,
            'failed_count': self.failed_count,
            'total_history': len(self.history)
        }

    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {e}")
        self.driver = None
