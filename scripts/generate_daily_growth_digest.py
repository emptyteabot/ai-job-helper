from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.business_service import BusinessService

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


def main() -> int:
    base_url = os.getenv("DIGEST_BASE_URL", "").strip().rstrip("/")

    if base_url and requests is not None:
        metrics = {}
        feedback = {}
        try:
            proof = requests.get(base_url + "/api/business/public-proof", timeout=30).json()
            ready = requests.get(base_url + "/api/ready", timeout=30).json()
            inv = requests.get(base_url + "/api/investor/readiness", timeout=30).json()
            metrics = {
                "leads": {"total": proof.get("leads_total", 0), "last_7d": None},
                "feedback": {"total": proof.get("feedback_total", 0), "last_7d": None},
                "funnel": {
                    "uploads": proof.get("uploads_total", 0),
                    "process_runs": proof.get("process_runs_total", 0),
                    "searches": None,
                    "applies": None,
                    "upload_to_process_pct": None,
                    "process_to_search_pct": None,
                    "search_to_apply_pct": None,
                },
                "ready": ready,
                "investor_readiness": inv,
            }
            feedback = {
                "total": proof.get("feedback_total", 0),
                "last_days": 7,
                "last_days_count": None,
                "avg_rating_last_days": None,
                "recent": [],
            }
        except Exception as e:
            metrics = {"error": f"remote digest fetch failed: {e}"}
            feedback = {}
    else:
        svc = BusinessService()
        metrics = svc.metrics()
        feedback = svc.feedback_summary(days=7, limit=20)
    now = datetime.now(UTC)
    day = now.strftime("%Y-%m-%d")

    out_dir = Path("docs/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md = out_dir / f"daily_growth_digest_{day}.md"
    out_json = out_dir / f"daily_growth_digest_{day}.json"

    leads = metrics.get("leads", {})
    funnel = metrics.get("funnel", {})

    lines = [
        f"# Daily Growth Digest - {day}",
        "",
        f"- Data source: {'remote' if base_url else 'local'}",
        f"- Base URL: {base_url or '(local db)'}",
        "",
        "## Core Metrics",
        f"- Leads total: {leads.get('total', 0)}",
        f"- Leads last 7d: {leads.get('last_7d', 0)}",
        f"- Feedback total: {metrics.get('feedback', {}).get('total', 0)}",
        f"- Feedback last 7d: {metrics.get('feedback', {}).get('last_7d', 0)}",
        f"- Uploads: {funnel.get('uploads', 0)}",
        f"- Process runs: {funnel.get('process_runs', 0)}",
        f"- Searches: {funnel.get('searches', 0)}",
        f"- Applies: {funnel.get('applies', 0)}",
        "",
        "## Conversion",
        f"- upload -> process: {funnel.get('upload_to_process_pct', 0)}%",
        f"- process -> search: {funnel.get('process_to_search_pct', 0)}%",
        f"- search -> apply: {funnel.get('search_to_apply_pct', 0)}%",
        "",
        "## Feedback Snapshot",
        f"- Avg rating (7d): {feedback.get('avg_rating_last_days')}",
    ]

    recent = feedback.get("recent", [])[:10]
    if recent:
        lines.append("- Recent feedback:")
        for row in recent:
            msg = (row.get("message") or "").replace("\n", " ").strip()
            if len(msg) > 100:
                msg = msg[:100] + "..."
            lines.append(
                f"  - [{row.get('created_at', '')}] rating={row.get('rating')} "
                f"category={row.get('category')}: {msg}"
            )
    else:
        lines.append("- Recent feedback: (none)")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "source": "remote" if base_url else "local",
                "base_url": base_url or None,
                "metrics": metrics,
                "feedback_summary": feedback,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(str(out_md))
    print(str(out_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
