"""Auto-apply configuration and validation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class AutoApplyConfig:
    """Runtime config for auto-apply workflows."""

    # Platform selection.
    platform: str = "linkedin"  # linkedin, boss, zhilian

    # Session limits.
    max_apply_per_session: int = 50
    max_apply_per_day: int = 200

    # Search settings.
    keywords: str = ""
    location: str = ""
    experience_level: List[str] = field(default_factory=lambda: ["entry", "mid", "senior"])
    job_type: List[str] = field(default_factory=lambda: ["full-time"])

    # Filtering settings.
    company_blacklist: List[str] = field(default_factory=list)
    company_whitelist: List[str] = field(default_factory=list)
    title_blacklist: List[str] = field(default_factory=list)
    min_salary: int = 0
    max_salary: int = 0

    # Execution controls.
    random_delay_min: float = 2.0
    random_delay_max: float = 5.0
    apply_interval_seconds: float = 0.0
    pause_before_submit: bool = False
    enable_job_scoring: bool = True
    dedupe_before_apply: bool = True

    # Browser settings.
    headless: bool = False
    use_profile: bool = True
    profile_path: str = ""

    # AI settings.
    use_ai_answers: bool = True
    ai_model: str = "deepseek"

    # Reliability settings.
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "max_apply_per_session": self.max_apply_per_session,
            "max_apply_per_day": self.max_apply_per_day,
            "keywords": self.keywords,
            "location": self.location,
            "experience_level": self.experience_level,
            "job_type": self.job_type,
            "company_blacklist": self.company_blacklist,
            "company_whitelist": self.company_whitelist,
            "title_blacklist": self.title_blacklist,
            "min_salary": self.min_salary,
            "max_salary": self.max_salary,
            "random_delay_min": self.random_delay_min,
            "random_delay_max": self.random_delay_max,
            "apply_interval_seconds": self.apply_interval_seconds,
            "pause_before_submit": self.pause_before_submit,
            "enable_job_scoring": self.enable_job_scoring,
            "dedupe_before_apply": self.dedupe_before_apply,
            "headless": self.headless,
            "use_profile": self.use_profile,
            "profile_path": self.profile_path,
            "use_ai_answers": self.use_ai_answers,
            "ai_model": self.ai_model,
            "max_retries": self.max_retries,
            "retry_backoff_seconds": self.retry_backoff_seconds,
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoApplyConfig":
        return cls(**{k: v for k, v in (data or {}).items() if k in cls.__annotations__})


DEFAULT_CONFIG = AutoApplyConfig()


PLATFORM_CONFIGS = {
    "linkedin": {
        "base_url": "https://www.linkedin.com",
        "jobs_url": "https://www.linkedin.com/jobs/search/",
        "easy_apply_filter": True,
        "supports_ai_answers": True,
    },
    "boss": {
        "base_url": "https://www.zhipin.com",
        "jobs_url": "https://www.zhipin.com/web/geek/job",
        "easy_apply_filter": False,
        "supports_ai_answers": False,
    },
    "zhilian": {
        "base_url": "https://www.zhaopin.com",
        "jobs_url": "https://www.zhaopin.com/sou/",
        "easy_apply_filter": False,
        "supports_ai_answers": False,
    },
}


def get_platform_config(platform: str) -> Dict[str, Any]:
    return PLATFORM_CONFIGS.get(platform, {})


def validate_config(config: AutoApplyConfig) -> Tuple[bool, str]:
    if config.platform not in PLATFORM_CONFIGS:
        return False, f"unsupported platform: {config.platform}"

    if config.max_apply_per_session <= 0:
        return False, "max_apply_per_session must be > 0"
    if config.max_apply_per_session > 200:
        return False, "max_apply_per_session must be <= 200"

    if config.random_delay_min < 0:
        return False, "random_delay_min must be >= 0"
    if config.random_delay_max < config.random_delay_min:
        return False, "random_delay_max must be >= random_delay_min"

    if config.apply_interval_seconds < 0:
        return False, "apply_interval_seconds must be >= 0"

    if config.max_retries < 0 or config.max_retries > 10:
        return False, "max_retries must be between 0 and 10"
    if config.retry_backoff_seconds < 0:
        return False, "retry_backoff_seconds must be >= 0"

    if not config.keywords and not config.location:
        return False, "keywords or location is required"

    return True, ""
