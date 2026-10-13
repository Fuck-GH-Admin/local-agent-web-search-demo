#!/usr/bin/env python3
"""Opt-in B01 real search probe. Never runs as part of offline pytest."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path

import httpx

from local_search_demo.search.searxng import SearXNGClient

ROOT = Path(__file__).resolve().parents[1]


def classify_live(attempts: list[dict]) -> str:
    if not attempts:
        return "NOT_RUN"
    if any(x["has_valid_results"] for x in attempts):
        return "LIVE_PASS"
    kinds = {
        err["kind"]
        for x in attempts
        for err in x["result"].get("errors", [])
    }
    if kinds & {"NETWORK_ERROR", "TIMEOUT"}:
        return "BLOCKED_LOCAL"
    if kinds & {"JSON_FORBIDDEN", "INVALID_JSON", "INVALID_RESPONSE"}:
        return "CONFIG_ERROR"
    if kinds & {"RATE_LIMITED", "HTTP_ERROR"}:
        return "SERVICE_ERROR"
    if "UPSTREAM_UNRESPONSIVE" in kinds:
        return "UPSTREAM_BLOCKED"
    if all(x["result"].get("status") == "EMPTY" for x in attempts):
        return "NO_RESULTS"
    return "SERVICE_ERROR"


async def probe(base_url: str, timeout: float) -> dict:
    attempts = []
    async with httpx.AsyncClient() as client:
        adapter = SearXNGClient(base_url, client)
        for query in ["python asyncio documentation", "电磁干扰 科学研究"]:
            started_at = datetime.now(timezone.utc).isoformat()
            result = await adapter.search(query, limit=5, timeout=timeout)
            attempts.append({
                "query": query,
                "started_at_utc": started_at,
                "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                "result": result.model_dump(mode="json"),
                "has_valid_results": result.status == "PASS" and bool(result.items),
            })
    return {
        "batch": "B01",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "searxng_base_url": base_url,
        "live_status": classify_live(attempts),
        "attempts": attempts,
        "note": "Live SearXNG results; this is not an offline pytest result.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/B01/search-smoke.json")
    args = parser.parse_args()
    report = asyncio.run(probe(args.base_url, args.timeout))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["live_status"],
        "results": [len(x["result"]["items"]) for x in report["attempts"]],
        "output": str(args.output),
    }, ensure_ascii=False))
    return 0 if report["live_status"] == "LIVE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
