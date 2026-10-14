#!/usr/bin/env python3
"""Optional B06 target-host direct HTTPS smoke for DNS-pinned public-only transport.

Runs only on explicit invocation. No model/key needed, no proxies, no sensitive
URL input; results store status and bounded metadata only.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path

import httpx
from local_search_demo.agent.safe_http import SafePublicTransport, create_safe_agent_client, UnsafeDestination

ROOT = Path(__file__).resolve().parents[1]
SITES = ["https://example.org/", "https://docs.python.org/3/library/asyncio.html"]


async def check() -> dict:
    rows = []
    transport = SafePublicTransport()
    async with create_safe_agent_client(transport=transport) as client:
        for url in SITES:
            record = {"url": url, "status": "BLOCKED", "http_status": None, "bytes": 0}
            try:
                async with client.stream("GET", url, timeout=8.0) as response:
                    record["http_status"] = response.status_code
                    record["final_url"] = str(response.url)
                    content_bytes = 0
                    async for part in response.aiter_bytes():
                        content_bytes += len(part)
                        if content_bytes > 1_000_000:
                            raise ValueError("response too large")
                    record["bytes"] = content_bytes
                    record["status"] = "PASS" if response.status_code == 200 and content_bytes else "FAIL"
            except (httpx.HTTPError, UnsafeDestination, OSError, ValueError) as exc:
                record["error_kind"] = type(exc).__name__
            rows.append(record)
    return {
        "batch": "B06",
        "kind": "actual_public_HTTPS_with_pinned_IP_TLS",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "proxy_environment_used": False,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "BLOCKED_OR_FAIL",
        "rows": rows,
        "dns_and_pinned_connection_audit": transport.audit,
        "note": "This tests real HTTPS connectivity; it does not prove an LLM will call tools correctly.",
    }


def main() -> int:
    report = asyncio.run(check())
    path = ROOT / "reports/B06/safe-http-live.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(path)}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
