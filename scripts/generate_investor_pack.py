import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import web_app


def build_markdown(snapshot: dict) -> str:
    p = snapshot.get("pillars", {})
    m = snapshot.get("metrics", {})
    funnel = m.get("funnel", {})
    leads = m.get("leads", {})
    st = m.get("stability", {})
    hi = snapshot.get("highlights", {})
    tgt = snapshot.get("next_30d_targets", {})

    lines = [
        "# Investor Pack Snapshot",
        "",
        f"- generated_at_utc: {datetime.now(UTC).isoformat()}",
        f"- status: {snapshot.get('status')}",
        f"- overall_score: {snapshot.get('overall_score')}",
        "",
        "## Pillars",
        f"- product: {p.get('product')}",
        f"- traction: {p.get('traction')}",
        f"- reliability: {p.get('reliability')}",
        f"- go_to_market: {p.get('go_to_market')}",
        "",
        "## Highlights",
        f"- provider_mode: {hi.get('provider_mode')}",
        f"- enterprise_api_configured: {hi.get('enterprise_api_configured')}",
        f"- global_fallback_enabled: {hi.get('global_fallback_enabled')}",
        f"- cloud_cache_total: {hi.get('cloud_cache_total')}",
        "",
        "## Funnel",
        f"- uploads: {funnel.get('uploads', 0)}",
        f"- process_runs: {funnel.get('process_runs', 0)}",
        f"- searches: {funnel.get('searches', 0)}",
        f"- applies: {funnel.get('applies', 0)}",
        f"- upload_to_process_pct: {funnel.get('upload_to_process_pct', 0)}",
        f"- process_to_search_pct: {funnel.get('process_to_search_pct', 0)}",
        f"- search_to_apply_pct: {funnel.get('search_to_apply_pct', 0)}",
        f"- process_success_pct: {funnel.get('process_success_pct', 0)}",
        f"- leads_total: {leads.get('total', 0)}",
        f"- leads_7d: {leads.get('last_7d', 0)}",
        f"- api_errors: {st.get('api_errors', 0)}",
        "",
        "## Next 30 Days Targets",
        f"- uploads: {tgt.get('uploads')}",
        f"- process_runs: {tgt.get('process_runs')}",
        f"- searches: {tgt.get('searches')}",
        f"- applies: {tgt.get('applies')}",
        f"- leads_total: {tgt.get('leads_total')}",
        "",
        "## Suggested Pitch Angles",
        "- We converted AI output into actionable CN-market job links with resilient fallback modes.",
        "- We built release-gated observability and readiness checks to reduce operational risk.",
        "- We now run weekly growth reporting automation for data-driven GTM iteration.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate investor pack markdown/json from live snapshot logic.")
    parser.add_argument("--out-dir", default="docs/investor")
    args = parser.parse_args()

    snap = web_app._build_investor_readiness_snapshot()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    day = datetime.now(UTC).date().isoformat()

    md_path = out_dir / f"investor_pack_{day}.md"
    json_path = out_dir / f"investor_pack_{day}.json"

    md_path.write_text(build_markdown(snap), encoding="utf-8")
    json_path.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")

    print(str(md_path))
    print(str(json_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
