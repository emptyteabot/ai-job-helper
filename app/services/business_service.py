from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional


class BusinessService:
    """Persistent lead + funnel tracking for growth and monetization."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("APP_DATA_DB_PATH", "data/app_data.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._conn()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS leads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        name TEXT,
                        company TEXT,
                        use_case TEXT,
                        budget TEXT,
                        source TEXT,
                        note TEXT,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_name TEXT NOT NULL,
                        payload_json TEXT,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_name_time ON events(event_name, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at)")
                conn.commit()
            finally:
                conn.close()

    def add_lead(
        self,
        email: str,
        name: str = "",
        company: str = "",
        use_case: str = "",
        budget: str = "",
        source: str = "landing",
        note: str = "",
    ) -> Dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        with self._lock:
            conn = self._conn()
            try:
                cur = conn.execute(
                    """
                    INSERT OR REPLACE INTO leads(email, name, company, use_case, budget, source, note, created_at)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (email.strip().lower(), name.strip(), company.strip(), use_case.strip(), budget.strip(), source.strip(), note.strip(), now),
                )
                conn.commit()
                lead_id = cur.lastrowid
            finally:
                conn.close()
        self.track_event("lead_captured", {"email": email, "source": source, "budget": budget})
        return {"lead_id": lead_id, "created_at": now}

    def track_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        now = datetime.now(UTC).isoformat()
        payload_json = json.dumps(payload or {}, ensure_ascii=False)
        with self._lock:
            conn = self._conn()
            try:
                conn.execute(
                    "INSERT INTO events(event_name, payload_json, created_at) VALUES(?, ?, ?)",
                    (event_name.strip(), payload_json, now),
                )
                conn.commit()
            finally:
                conn.close()

    def _count(self, conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
        row = conn.execute(sql, params).fetchone()
        return int(row[0] if row and row[0] is not None else 0)

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            conn = self._conn()
            try:
                total_leads = self._count(conn, "SELECT COUNT(*) FROM leads")
                leads_7d = self._count(
                    conn,
                    "SELECT COUNT(*) FROM leads WHERE created_at >= ?",
                    ((datetime.now(UTC) - timedelta(days=7)).isoformat(),),
                )

                uploads = self._count(conn, "SELECT COUNT(*) FROM events WHERE event_name='resume_uploaded'")
                process_runs = self._count(conn, "SELECT COUNT(*) FROM events WHERE event_name='resume_processed'")
                searches = self._count(conn, "SELECT COUNT(*) FROM events WHERE event_name='job_search'")
                applies = self._count(conn, "SELECT COUNT(*) FROM events WHERE event_name='job_apply'")

                processed_success = self._count(
                    conn,
                    "SELECT COUNT(*) FROM events WHERE event_name='resume_processed' AND json_extract(payload_json, '$.ok') = 1",
                )
                errors = self._count(conn, "SELECT COUNT(*) FROM events WHERE event_name='api_error'")
            finally:
                conn.close()

        upload_to_process = round((process_runs / uploads) * 100, 2) if uploads else 0.0
        process_to_search = round((searches / process_runs) * 100, 2) if process_runs else 0.0
        search_to_apply = round((applies / searches) * 100, 2) if searches else 0.0
        process_success_rate = round((processed_success / process_runs) * 100, 2) if process_runs else 0.0

        return {
            "leads": {
                "total": total_leads,
                "last_7d": leads_7d,
            },
            "funnel": {
                "uploads": uploads,
                "process_runs": process_runs,
                "searches": searches,
                "applies": applies,
                "upload_to_process_pct": upload_to_process,
                "process_to_search_pct": process_to_search,
                "search_to_apply_pct": search_to_apply,
                "process_success_pct": process_success_rate,
            },
            "stability": {
                "api_errors": errors,
            },
            "generated_at": datetime.now(UTC).isoformat(),
        }
