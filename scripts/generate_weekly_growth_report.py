import argparse
import os
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.business_service import BusinessService


def daily_event_counts(db_path: str, days: int = 7) -> List[Dict[str, int]]:
    end = datetime.now(UTC).date()
    start = end - timedelta(days=days - 1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT substr(created_at,1,10) AS day, event_name, COUNT(*) AS c
            FROM events
            WHERE created_at >= ?
            GROUP BY day, event_name
            ORDER BY day ASC
            """,
            (start.isoformat(),),
        ).fetchall()
    finally:
        conn.close()

    by_day: Dict[str, Dict[str, int]] = {}
    for r in rows:
        d = str(r["day"])
        by_day.setdefault(d, {})
        by_day[d][str(r["event_name"])] = int(r["c"])

    out: List[Dict[str, int]] = []
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        event = by_day.get(d, {})
        out.append(
            {
                "day": d,
                "resume_uploaded": int(event.get("resume_uploaded", 0)),
                "resume_processed": int(event.get("resume_processed", 0)),
                "job_search": int(event.get("job_search", 0)),
                "job_apply": int(event.get("job_apply", 0)),
                "api_error": int(event.get("api_error", 0)),
            }
        )
    return out


def build_markdown(metrics: Dict, timeline: List[Dict[str, int]]) -> str:
    funnel = metrics.get("funnel", {})
    leads = metrics.get("leads", {})
    st = metrics.get("stability", {})
    now = datetime.now(UTC).isoformat()

    lines = [
        "# Weekly Growth Report",
        "",
        f"- generated_at_utc: {now}",
        "",
        "## Summary",
        f"- leads_total: {leads.get('total', 0)}",
        f"- leads_7d: {leads.get('last_7d', 0)}",
        f"- uploads: {funnel.get('uploads', 0)}",
        f"- process_runs: {funnel.get('process_runs', 0)}",
        f"- searches: {funnel.get('searches', 0)}",
        f"- applies: {funnel.get('applies', 0)}",
        f"- upload_to_process_pct: {funnel.get('upload_to_process_pct', 0)}",
        f"- process_to_search_pct: {funnel.get('process_to_search_pct', 0)}",
        f"- search_to_apply_pct: {funnel.get('search_to_apply_pct', 0)}",
        f"- process_success_pct: {funnel.get('process_success_pct', 0)}",
        f"- api_errors: {st.get('api_errors', 0)}",
        "",
        "## Daily Funnel",
        "| day | upload | process | search | apply | api_error |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for d in timeline:
        lines.append(
            f"| {d['day']} | {d['resume_uploaded']} | {d['resume_processed']} | "
            f"{d['job_search']} | {d['job_apply']} | {d['api_error']} |"
        )

    lines.extend(
        [
            "",
            "## Next Actions",
            "- 优先优化 upload -> process 转化链路文案和引导。",
            "- 若 job_search 下滑，检查数据源风控与回退命中率。",
            "- 针对高错误日做日志回放并修复前 3 大异常。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate weekly growth report from app_data.db")
    parser.add_argument("--db-path", default=os.getenv("APP_DATA_DB_PATH", "data/app_data.db"))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--out-dir", default="docs/reports")
    args = parser.parse_args()

    svc = BusinessService(db_path=args.db_path)
    metrics = svc.metrics()
    timeline = daily_event_counts(args.db_path, days=max(1, args.days))
    report = build_markdown(metrics, timeline)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"weekly_growth_{datetime.now(UTC).date().isoformat()}.md"
    out_path.write_text(report, encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
