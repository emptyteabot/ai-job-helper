#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

PASS = "PASS"
ASSISTED = "ASSISTED"
FALLBACK = "FALLBACK"
FAIL = "FAIL"

STATUS_PRIORITY: Dict[str, int] = {
    PASS: 0,
    ASSISTED: 1,
    FALLBACK: 2,
    FAIL: 3,
}
STATUS_ORDER = (PASS, ASSISTED, FALLBACK, FAIL)
PRIORITY_TO_STATUS = {priority: status for status, priority in STATUS_PRIORITY.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run acceptance + smoke tools and emit a combined status report")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default="Acceptance123!")
    parser.add_argument("--keyword", default="Python backend")
    parser.add_argument("--city", default="Shenzhen")
    parser.add_argument(
        "--acceptance-report",
        default="scripts/.status/acceptance.json",
        help="Write the acceptance tool summary to this file",
    )
    parser.add_argument(
        "--smoke-report",
        default="scripts/.status/smoke_mainline.json",
        help="Write the smoke tool summary to this file",
    )
    parser.add_argument(
        "--final-report",
        default="scripts/.status/final_report.txt",
        help="Write the combined deliverable report to this file",
    )
    return parser.parse_args()


def run_tool(command: List[str], name: str) -> subprocess.CompletedProcess[str]:
    print(f"\n=== Running {name} ===")
    return subprocess.run(command, check=False, text=True)


def load_report(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"error": f"failed to parse {path.name}: {exc}"}


def combine_counts(reports: List[Dict[str, Any]]) -> Counter[str]:
    totals: Counter[str] = Counter()
    for report in reports:
        for status, count in (report.get("counts") or {}).items():
            totals[status] += count
    return totals


def collect_non_pass_details(report: Dict[str, Any]) -> List[str]:
    non_pass_lines: List[str] = []
    for record in report.get("records") or []:
        status = record.get("status")
        if status == PASS:
            continue
        label = record.get("label") or record.get("message") or "<step>"
        detail = record.get("detail") or record.get("message") or ""
        detail = f" {detail}".strip()
        non_pass_lines.append(f"{status}: {label}{detail}")
    return non_pass_lines


def print_summary(tool_reports: List[Dict[str, Any]], combined_counts: Counter[str], overall_status: str) -> None:
    print("\nFINAL STATUS VIEW")
    for status in STATUS_ORDER:
        print(f"  {status}: {combined_counts.get(status, 0)}")
    print(f"\nVERDICT: {overall_status}")
    print("\nTool details:")
    for tool in tool_reports:
        name = tool["name"]
        exit_code = tool["exit_code"]
        report = tool["report"]
        status = report.get("overall_status", "<missing>")
        print(f"  {name}: exit={exit_code} overall={status}")
        summary_lines = report.get("summary_lines") or []
        if summary_lines:
            for line in summary_lines:
                print(f"    - {line}")
        elif "error" in report:
            print(f"    - {report['error']}")


def write_final_report(
    path: Path,
    combined_counts: Counter[str],
    overall_status: str,
    tool_reports: List[Dict[str, Any]],
) -> None:
    lines: List[str] = []
    lines.append("FINAL DELIVERABLE REPORT")
    lines.append(f"Overall verdict: {overall_status}")
    lines.append("\nStatus counts:")
    for status in STATUS_ORDER:
        lines.append(f"  {status}: {combined_counts.get(status, 0)}")
    non_pass_lines: List[str] = []
    for tool in tool_reports:
        report = tool["report"]
        non_pass = collect_non_pass_details(report)
        if non_pass:
            non_pass_lines.append(f"{tool['name']} non-PASS steps:")
            for entry in non_pass:
                non_pass_lines.append(f"    {entry}")
    if non_pass_lines:
        lines.append("\nNon-PASS observations:")
        lines.extend(non_pass_lines)
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Final deliverable report written to {path}")


def make_command(args: argparse.Namespace, entrypoint: Path, extra_args: List[str]) -> List[str]:
    cmd = [
        sys.executable,
        str(entrypoint),
        f"--base-url={args.base_url}",
        f"--email={args.email}",
        f"--password={args.password}",
    ]
    cmd.extend(extra_args)
    return cmd


def main() -> int:
    args = parse_args()
    if not args.email:
        args.email = f"report-{int(time.time())}@agenthelpjob.com"
    base_dir = Path(__file__).resolve().parent
    repo_root = base_dir.parent
    acceptance_report = Path(args.acceptance_report)
    smoke_report = Path(args.smoke_report)
    final_report = Path(args.final_report)
    if not acceptance_report.is_absolute():
        acceptance_report = repo_root / acceptance_report
    if not smoke_report.is_absolute():
        smoke_report = repo_root / smoke_report
    if not final_report.is_absolute():
        final_report = repo_root / final_report

    tool_entries = [
        {
            "name": "acceptance",
            "cmd": make_command(
                args,
                base_dir / "acceptance.py",
                [
                    f"--status-report={acceptance_report}",
                    f"--keyword={args.keyword}",
                    f"--city={args.city}",
                ],
            ),
            "report": acceptance_report,
        },
        {
            "name": "smoke_mainline",
            "cmd": make_command(
                args,
                base_dir / "smoke_mainline.py",
                [
                    f"--status-report={smoke_report}",
                    f"--keyword={args.keyword}",
                    f"--city={args.city}",
                ],
            ),
            "report": smoke_report,
        },
    ]

    tool_reports: List[Dict[str, Any]] = []
    highest_priority = STATUS_PRIORITY[PASS]
    exit_code = 0

    for entry in tool_entries:
        result = run_tool(entry["cmd"], entry["name"])
        if result.returncode != 0:
            exit_code = 1
        report = load_report(entry["report"])
        if report.get("overall_status"):
            priority = STATUS_PRIORITY.get(report["overall_status"], 0)
            highest_priority = max(highest_priority, priority)
        tool_reports.append({"name": entry["name"], "exit_code": result.returncode, "report": report})

    combined_counts = combine_counts([tool["report"] for tool in tool_reports])
    overall_status = PRIORITY_TO_STATUS.get(highest_priority, PASS)
    print_summary(tool_reports, combined_counts, overall_status)
    write_final_report(final_report, combined_counts, overall_status, tool_reports)
    return 1 if exit_code or overall_status in {FALLBACK, FAIL} else 0


if __name__ == "__main__":
    sys.exit(main())
