#!/usr/bin/env python3
"""Smoke check for interview experience source collector endpoint."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

import requests


REQUIRED_KEYS = {"title", "summary", "source", "url", "published_at"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke check /api/interview/experiences/search")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--keywords", default="python backend,ai engineer", help="Comma-separated keywords")
    parser.add_argument("--location", default="shanghai", help="Location hint")
    parser.add_argument("--sources", default="nowcoder,xiaohongshu", help="Comma-separated sources")
    parser.add_argument("--limit", type=int, default=8, help="Result limit")
    return parser.parse_args()


def fail(msg: str, payload: Any = None) -> int:
    print(f"[FAIL] {msg}")
    if payload is not None:
        try:
            print(json.dumps(payload, ensure_ascii=False, indent=2)[:1200])
        except Exception:
            print(str(payload)[:1200])
    return 1


def request_items(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.get(url, params=params, timeout=45)
    body: Dict[str, Any] = resp.json()
    if resp.status_code != 200:
        raise RuntimeError(f"http status={resp.status_code} body={json.dumps(body, ensure_ascii=False)[:400]}")
    if not body.get("success"):
        raise RuntimeError(f"success flag false body={json.dumps(body, ensure_ascii=False)[:400]}")
    return body


def validate_items(items: List[Dict[str, Any]], expected_sources: List[str]) -> None:
    expected = {s.strip().lower() for s in expected_sources if s and s.strip()}
    for idx, it in enumerate(items[:8], 1):
        miss = [k for k in REQUIRED_KEYS if k not in it]
        if miss:
            raise RuntimeError(f"item#{idx} missing keys={miss}")
        src = str(it.get("source") or "").strip().lower()
        if expected and src and src != "other" and src not in expected:
            raise RuntimeError(f"item#{idx} source mismatch src={src} expected={sorted(expected)}")


def main() -> int:
    args = parse_args()
    base = args.base_url.rstrip("/")
    url = f"{base}/api/interview/experiences/search"
    params = {
        "keywords": args.keywords,
        "location": args.location,
        "sources": args.sources,
        "limit": max(1, min(int(args.limit), 30)),
    }

    try:
        body = request_items(url, params)
        items: List[Dict[str, Any]] = body.get("items") or []
        if not isinstance(items, list):
            return fail("items is not a list", body)
        validate_items(items, (args.sources or "").split(","))

        # Source filtering spot checks
        for only_source in ("nowcoder", "xiaohongshu"):
            spot_params = dict(params)
            spot_params["sources"] = only_source
            spot_body = request_items(url, spot_params)
            spot_items: List[Dict[str, Any]] = spot_body.get("items") or []
            validate_items(spot_items, [only_source])
    except Exception as exc:
        return fail(f"smoke failed: {exc}")

    print("[PASS] /api/interview/experiences/search")
    print(f"total={len(items)} sources={body.get('sources')}")
    if items:
        print("sample=", json.dumps(items[0], ensure_ascii=False)[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
