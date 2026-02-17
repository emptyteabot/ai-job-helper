"""
自动投递配置管理
"""

from typing import Dict, Any, List
import os
from dataclasses import dataclass, field


@dataclass
class AutoApplyConfig:
    """自动投递配置"""

    # 平台配置
    platform: str = "linkedin"  # linkedin, boss, zhilian

    # 投递限制
    max_apply_per_session: int = 50
    max_apply_per_day: int = 200

    # 搜索配置
    keywords: str = ""
    location: str = ""
    experience_level: List[str] = field(default_factory=lambda: ["entry", "mid", "senior"])
    job_type: List[str] = field(default_factory=lambda: ["full-time"])

    # 过滤配置
    company_blacklist: List[str] = field(default_factory=list)
    company_whitelist: List[str] = field(default_factory=list)
    title_blacklist: List[str] = field(default_factory=list)
    min_salary: int = 0
    max_salary: int = 0

    # 行为配置
    random_delay_min: int = 2  # 秒
    random_delay_max: int = 5  # 秒
    pause_before_submit: bool = False  # 提交前暂停人工审核

    # 浏览器配置
    headless: bool = False
    use_profile: bool = True  # 使用浏览器配置文件（保持登录）
    profile_path: str = ""

    # AI 配置
    use_ai_answers: bool = True  # 使用 AI 回答附加问题
    ai_model: str = "deepseek"

    # 安全配置
    max_retries: int = 3
    timeout: int = 30  # 秒

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'platform': self.platform,
            'max_apply_per_session': self.max_apply_per_session,
            'max_apply_per_day': self.max_apply_per_day,
            'keywords': self.keywords,
            'location': self.location,
            'experience_level': self.experience_level,
            'job_type': self.job_type,
            'company_blacklist': self.company_blacklist,
            'company_whitelist': self.company_whitelist,
            'title_blacklist': self.title_blacklist,
            'min_salary': self.min_salary,
            'max_salary': self.max_salary,
            'random_delay_min': self.random_delay_min,
            'random_delay_max': self.random_delay_max,
            'pause_before_submit': self.pause_before_submit,
            'headless': self.headless,
            'use_profile': self.use_profile,
            'profile_path': self.profile_path,
            'use_ai_answers': self.use_ai_answers,
            'ai_model': self.ai_model,
            'max_retries': self.max_retries,
            'timeout': self.timeout
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutoApplyConfig':
        """从字典创建配置"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


# 默认配置
DEFAULT_CONFIG = AutoApplyConfig()


# 平台特定配置
PLATFORM_CONFIGS = {
    'linkedin': {
        'base_url': 'https://www.linkedin.com',
        'jobs_url': 'https://www.linkedin.com/jobs/search/',
        'easy_apply_filter': True,
        'supports_ai_answers': True
    },
    'boss': {
        'base_url': 'https://www.zhipin.com',
        'jobs_url': 'https://www.zhipin.com/web/geek/job',
        'easy_apply_filter': False,
        'supports_ai_answers': False
    },
    'zhilian': {
        'base_url': 'https://www.zhaopin.com',
        'jobs_url': 'https://www.zhaopin.com/sou/',
        'easy_apply_filter': False,
        'supports_ai_answers': False
    }
}


def get_platform_config(platform: str) -> Dict[str, Any]:
    """获取平台特定配置"""
    return PLATFORM_CONFIGS.get(platform, {})


def validate_config(config: AutoApplyConfig) -> tuple[bool, str]:
    """
    验证配置有效性

    Returns:
        (is_valid, error_message)
    """
    if config.platform not in PLATFORM_CONFIGS:
        return False, f"不支持的平台: {config.platform}"

    if config.max_apply_per_session <= 0:
        return False, "每次投递数量必须大于0"

    if config.max_apply_per_session > 200:
        return False, "每次投递数量不能超过200（避免被封号）"

    if config.random_delay_min < 1:
        return False, "最小延迟不能小于1秒"

    if config.random_delay_max < config.random_delay_min:
        return False, "最大延迟不能小于最小延迟"

    if not config.keywords and not config.location:
        return False, "关键词和地点至少需要填写一个"

    return True, ""
