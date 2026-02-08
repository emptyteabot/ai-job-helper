from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class JobSearchParams:
    keywords: List[str]
    location: Optional[str] = None
    salary_min: Optional[int] = None
    experience: Optional[str] = None
    limit: int = 50


class JobProvider:
    """
    A provider returns job postings in the project's internal schema.

    NOTE: "apply" is not implemented here because most sources do not provide a
    programmatic apply API. The web layer can still return an apply link.
    """

    name: str = "base"

    def search_jobs(self, params: JobSearchParams) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return None

