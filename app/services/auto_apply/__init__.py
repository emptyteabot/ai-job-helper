"""
自动投递模块
整合 GitHub 高星项目，实现自动化简历投递
"""

from .base_applier import BaseApplier
from .boss_applier import BossApplier
from .linkedin_applier import LinkedInApplier
from .zhilian_applier import ZhilianApplier

__all__ = ['BaseApplier', 'BossApplier', 'LinkedInApplier', 'ZhilianApplier']
