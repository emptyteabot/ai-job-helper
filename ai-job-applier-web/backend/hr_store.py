from __future__ import annotations

import json
import re
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class HRStore:
    VALID_ACTIONS = {"like", "pass", "hold"}
    SKILL_SPLIT = re.compile(r"[,;/|\n]+")
    YEARS_RE = re.compile(r"(\d{1,2})\s*(?:\+)?\s*(?:years?|yrs?|年)", re.I)

    def __init__(self, data_file: Path):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._data = self._load()

    def create_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            job_id = str(payload.get("job_id") or payload.get("id") or uuid.uuid4().hex)
            existing = self._data["jobs"].get(job_id, {})
            now = self._now()
            record = {
                "job_id": job_id,
                "id": job_id,
                "hr_id": str(payload.get("hr_id") or existing.get("hr_id") or "").strip(),
                "title": str(payload.get("title") or existing.get("title") or "").strip(),
                "company": str(payload.get("company") or existing.get("company") or "").strip(),
                "location": str(payload.get("location") or existing.get("location") or "").strip(),
                "skills": self._normalize_skills(payload.get("skills") or existing.get("skills") or []),
                "min_years": self._safe_int(payload.get("min_years"), existing.get("min_years", 0)),
                "status": str(payload.get("status") or existing.get("status") or "open").strip().lower(),
                "created_at": existing.get("created_at") or now,
                "updated_at": now,
            }
            self._data["jobs"][job_id] = record
            self._persist()
            return deepcopy(record)

    def list_jobs(self, hr_id: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = list(self._data["jobs"].values())
        if hr_id:
            jobs = [job for job in jobs if job.get("hr_id") == hr_id]
        jobs.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return [deepcopy(job) for job in jobs[: max(1, int(limit or 50))]]

    def upsert_candidate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            candidate_id = str(
                payload.get("candidate_id")
                or payload.get("id")
                or payload.get("user_id")
                or uuid.uuid4().hex
            )
            existing = self._data["candidates"].get(candidate_id, {})
            resume_text = str(payload.get("resume_text") or existing.get("resume_text") or "").strip()
            now = self._now()
            record = {
                "candidate_id": candidate_id,
                "id": candidate_id,
                "user_id": str(payload.get("user_id") or existing.get("user_id") or "").strip(),
                "phone": str(payload.get("phone") or existing.get("phone") or "").strip(),
                "nickname": str(payload.get("nickname") or existing.get("nickname") or "").strip(),
                "location": str(payload.get("location") or existing.get("location") or "").strip(),
                "skills": self._normalize_skills(payload.get("skills") or self._extract_skills(resume_text)),
                "years_experience": self._safe_int(
                    payload.get("years_experience"),
                    existing.get("years_experience", self._extract_years(resume_text)),
                ),
                "resume_text": resume_text,
                "resume_filename": str(payload.get("resume_filename") or existing.get("resume_filename") or "").strip(),
                "created_at": existing.get("created_at") or now,
                "updated_at": now,
            }
            self._data["candidates"][candidate_id] = record
            self._persist()
            return deepcopy(record)

    def list_candidates(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._lock:
            candidates = list(self._data["candidates"].values())
        candidates.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return [deepcopy(candidate) for candidate in candidates[: max(1, int(limit or 200))]]

    def match_candidates(self, job_id: str, hr_id: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            job = deepcopy(self._data["jobs"].get(job_id))
            candidates = list(self._data["candidates"].values())
        if not job:
            raise KeyError(f"job not found: {job_id}")
        if hr_id and job.get("hr_id") and job.get("hr_id") != hr_id:
            return []

        rows: List[Dict[str, Any]] = []
        for candidate in candidates:
            rows.append(self._score_pair(job, candidate))
        rows.sort(key=lambda item: item["score"], reverse=True)
        return rows[: max(1, int(limit or 50))]

    def record_action(self, actor: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if actor not in {"hr", "candidate"}:
            raise ValueError("actor must be hr or candidate")
        decision = self._normalize_action(payload.get("action") or payload.get("decision"))
        record = {
            "id": uuid.uuid4().hex,
            "actor": actor,
            "job_id": str(payload.get("job_id") or "").strip(),
            "candidate_id": str(payload.get("candidate_id") or "").strip(),
            "hr_id": str(payload.get("hr_id") or "").strip(),
            "decision": decision,
            "timestamp": self._now(),
        }
        if not record["job_id"] or not record["candidate_id"]:
            raise ValueError("job_id and candidate_id are required")
        with self._lock:
            self._data["actions"][actor].append(record)
            self._persist()
        return deepcopy(record)

    def list_mutual_matches(self, hr_id: str = "", job_id: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = deepcopy(self._data["jobs"])
            candidates = deepcopy(self._data["candidates"])
            hr_actions = list(self._data["actions"]["hr"])
            candidate_actions = list(self._data["actions"]["candidate"])

        liked_by_hr = {
            (row["job_id"], row["candidate_id"]): row
            for row in hr_actions
            if row.get("decision") == "like"
        }
        liked_by_candidate = {
            (row["job_id"], row["candidate_id"]): row
            for row in candidate_actions
            if row.get("decision") == "like"
        }

        matches: List[Dict[str, Any]] = []
        for pair in sorted(set(liked_by_hr) & set(liked_by_candidate)):
            one_job_id, one_candidate_id = pair
            if job_id and one_job_id != job_id:
                continue
            job = jobs.get(one_job_id)
            candidate = candidates.get(one_candidate_id)
            if not job or not candidate:
                continue
            if hr_id and job.get("hr_id") != hr_id:
                continue
            scored = self._score_pair(job, candidate)
            scored["hr_action"] = liked_by_hr[pair]
            scored["candidate_action"] = liked_by_candidate[pair]
            matches.append(scored)
            if len(matches) >= max(1, int(limit or 100)):
                break
        return matches

    def overview(self, hr_id: str = "") -> Dict[str, Any]:
        jobs = self.list_jobs(hr_id=hr_id, limit=10000)
        candidates = self.list_candidates(limit=10000)
        mutual_matches = self.list_mutual_matches(hr_id=hr_id, limit=10000)
        with self._lock:
            actions = list(self._data["actions"]["hr"]) + list(self._data["actions"]["candidate"])
        actions.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
        return {
            "jobs_count": len(jobs),
            "open_jobs": sum(1 for item in jobs if item.get("status") == "open"),
            "candidates_count": len(candidates),
            "mutual_matches": len(mutual_matches),
            "recent_actions": actions[:10],
        }

    def _score_pair(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
        job_skills = set(self._normalize_skills(job.get("skills")))
        candidate_skills = set(self._normalize_skills(candidate.get("skills")))
        matched_skills = sorted(job_skills & candidate_skills)

        score = 20
        if job_skills:
            score += min(60, len(matched_skills) * 18)

        job_location = str(job.get("location") or "").strip().lower()
        candidate_location = str(candidate.get("location") or "").strip().lower()
        location_match = bool(job_location and candidate_location and job_location in candidate_location)
        if location_match:
            score += 15

        years_gap = max(0, int(job.get("min_years") or 0) - int(candidate.get("years_experience") or 0))
        score -= min(20, years_gap * 4)

        resume_text = str(candidate.get("resume_text") or "").lower()
        title_tokens = [token for token in re.split(r"\s+", str(job.get("title") or "").lower()) if len(token) >= 3]
        keyword_hits = sum(1 for token in title_tokens if token in resume_text)
        score += min(10, keyword_hits * 2)

        return {
            "job_id": job.get("job_id") or job.get("id"),
            "candidate_id": candidate.get("candidate_id") or candidate.get("id"),
            "score": max(0, score),
            "matched_skills": matched_skills,
            "location_match": location_match,
            "years_gap": years_gap,
            "job": deepcopy(job),
            "candidate": deepcopy(candidate),
        }

    def _load(self) -> Dict[str, Any]:
        if not self.data_file.exists():
            return {"jobs": {}, "candidates": {}, "actions": {"hr": [], "candidate": []}}
        try:
            raw = json.loads(self.data_file.read_text(encoding="utf-8") or "{}")
        except Exception:
            raw = {}
        return {
            "jobs": raw.get("jobs", {}) if isinstance(raw.get("jobs"), dict) else {},
            "candidates": raw.get("candidates", {}) if isinstance(raw.get("candidates"), dict) else {},
            "actions": {
                "hr": raw.get("actions", {}).get("hr", []) if isinstance(raw.get("actions", {}).get("hr", []), list) else [],
                "candidate": raw.get("actions", {}).get("candidate", []) if isinstance(raw.get("actions", {}).get("candidate", []), list) else [],
            },
        }

    def _persist(self) -> None:
        self.data_file.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _normalize_skills(self, value: Any) -> List[str]:
        items: List[str] = []
        if isinstance(value, list):
            source = value
        else:
            source = self.SKILL_SPLIT.split(str(value or ""))
        seen = set()
        for raw in source:
            token = str(raw or "").strip()
            if not token:
                continue
            lowered = token.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            items.append(token)
        return items[:30]

    def _extract_skills(self, text: str) -> List[str]:
        known = [
            "python", "java", "golang", "go", "react", "vue", "typescript", "javascript",
            "docker", "kubernetes", "mysql", "postgresql", "redis", "fastapi", "django",
            "flask", "spring", "langchain", "rag", "pytorch", "tensorflow", "llm",
        ]
        lower_text = str(text or "").lower()
        found = [skill for skill in known if skill in lower_text]
        return found[:20]

    def _extract_years(self, text: str) -> int:
        years = [int(match.group(1)) for match in self.YEARS_RE.finditer(str(text or ""))]
        if not years:
            return 0
        return max(0, min(max(years), 30))

    def _normalize_action(self, value: Any) -> str:
        action = str(value or "").strip().lower()
        if action not in self.VALID_ACTIONS:
            raise ValueError("action must be one of like/pass/hold")
        return action

    def _safe_int(self, value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except Exception:
            return int(default or 0)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
