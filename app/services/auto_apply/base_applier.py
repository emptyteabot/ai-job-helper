"""Base class for platform-specific auto-apply implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List
import logging
import time

logger = logging.getLogger(__name__)


class BaseApplier(ABC):
    """Common orchestration logic shared by all appliers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.driver = None
        self.is_running = False
        self.state = "idle"
        self.applied_count = 0
        self.failed_count = 0
        self.history: List[Dict[str, Any]] = []

    @abstractmethod
    def login(self, email: str, password: str) -> bool:
        pass

    @abstractmethod
    def search_jobs(self, keywords: str, location: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def apply_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def _job_dedupe_key(self, job: Dict[str, Any]) -> str:
        if not isinstance(job, dict):
            return ""
        link = str(job.get("link") or job.get("apply_url") or job.get("url") or "").strip().lower()
        jid = str(job.get("id") or "").strip().lower()
        title = str(job.get("title") or job.get("job_title") or "").strip().lower()
        company = str(job.get("company") or "").strip().lower()
        return link or jid or f"{title}|{company}"

    def _normalize_ratio(self, value: Any) -> float:
        try:
            num = float(value)
        except Exception:
            return 0.0
        if num > 1.0:
            num = num / 100.0
        return max(0.0, min(1.0, num))

    def _score_job(self, job: Dict[str, Any]) -> float:
        title = str(job.get("title") or job.get("job_title") or "")
        location = str(job.get("location") or "")
        company = str(job.get("company") or "")
        match_ratio = self._normalize_ratio(job.get("match_rate") or job.get("match_score") or 0.0)

        score = match_ratio * 100.0

        keywords = str(self.config.get("keywords") or "").lower().split()
        title_l = title.lower()
        for kw in keywords:
            if kw and kw in title_l:
                score += 4.0

        target_location = str(self.config.get("location") or "").strip().lower()
        if target_location and target_location in location.lower():
            score += 5.0

        if company.strip():
            score += 1.0

        return score

    def _prepare_jobs(self, jobs: List[Dict[str, Any]], max_count: int) -> List[Dict[str, Any]]:
        dedupe_enabled = bool(self.config.get("dedupe_before_apply", True))
        scoring_enabled = bool(self.config.get("enable_job_scoring", True))

        prepared: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for job in jobs or []:
            if not isinstance(job, dict):
                continue
            if dedupe_enabled:
                key = self._job_dedupe_key(job)
                if not key or key in seen:
                    continue
                seen.add(key)
            prepared.append(job)

        if scoring_enabled:
            prepared.sort(key=self._score_job, reverse=True)

        safe_max = max(1, int(max_count or 50))
        return prepared[:safe_max]

    def _is_retryable_failure(self, result: Dict[str, Any]) -> bool:
        if result.get("success"):
            return False
        message = str(result.get("message") or "").lower()
        permanent_markers = [
            "already",
            "已投递",
            "blacklist",
            "黑名单",
            "缺少链接",
            "missing",
            "invalid",
            "不匹配",
        ]
        return not any(marker in message for marker in permanent_markers)

    def _delay_between_jobs(self) -> None:
        interval = float(self.config.get("apply_interval_seconds") or 0.0)
        if interval <= 0:
            min_delay = float(self.config.get("random_delay_min") or 0.0)
            max_delay = float(self.config.get("random_delay_max") or min_delay)
            interval = max(min_delay, max_delay)
        if interval > 0:
            time.sleep(interval)

    def batch_apply(self, jobs: List[Dict[str, Any]], max_count: int = 50) -> Dict[str, Any]:
        self.is_running = True
        self.state = "running"
        self.applied_count = 0
        self.failed_count = 0
        results: List[Dict[str, Any]] = []

        prepared_jobs = self._prepare_jobs(jobs, max_count)
        max_retries = max(0, int(self.config.get("max_retries") or 0))
        retry_backoff = max(0.0, float(self.config.get("retry_backoff_seconds") or 0.0))

        logger.info("Batch auto-apply started: prepared=%s target=%s", len(prepared_jobs), max_count)

        for idx, job in enumerate(prepared_jobs, 1):
            if not self.is_running:
                logger.info("Batch auto-apply stopped by signal")
                break

            title = str(job.get("title") or job.get("job_title") or "Unknown")
            attempt = 0
            final_result: Dict[str, Any] = {}

            while attempt <= max_retries and self.is_running:
                attempt += 1
                try:
                    logger.info("Applying [%s/%s] attempt=%s title=%s", idx, len(prepared_jobs), attempt, title)
                    result = self.apply_job(job) or {}
                    if not isinstance(result, dict):
                        result = {"success": False, "message": "apply_job returned non-dict", "job": job}
                except Exception as exc:
                    result = {
                        "success": False,
                        "message": str(exc),
                        "job": job,
                        "timestamp": datetime.now().isoformat(),
                    }
                    logger.exception("Apply job exception title=%s attempt=%s", title, attempt)

                result.setdefault("job", job)
                result.setdefault("timestamp", datetime.now().isoformat())
                result["attempts"] = attempt
                final_result = result

                if result.get("success"):
                    break
                if attempt > max_retries:
                    break
                if not self._is_retryable_failure(result):
                    break
                if retry_backoff > 0:
                    time.sleep(retry_backoff * attempt)

            if final_result.get("success"):
                self.applied_count += 1
            else:
                self.failed_count += 1

            results.append(final_result)
            self._save_history(final_result)

            if idx < len(prepared_jobs):
                self._delay_between_jobs()

        self.is_running = False
        if self.state != "stopped":
            self.state = "completed"

        summary = {
            "total_attempted": len(results),
            "prepared_count": len(prepared_jobs),
            "applied": self.applied_count,
            "failed": self.failed_count,
            "success_rate": self.applied_count / len(results) if results else 0,
            "results": results,
        }
        logger.info("Batch auto-apply completed: applied=%s failed=%s", self.applied_count, self.failed_count)
        return summary

    def stop(self) -> None:
        self.is_running = False
        self.state = "stopped"
        logger.info("Stop signal received")

    def _save_history(self, result: Dict[str, Any]) -> None:
        self.history.append(result)

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "is_running": self.is_running,
            "applied_count": self.applied_count,
            "failed_count": self.failed_count,
            "total_history": len(self.history),
        }

    def cleanup(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser driver closed")
            except Exception as exc:
                logger.error("Failed to close browser driver: %s", exc)
        self.driver = None
