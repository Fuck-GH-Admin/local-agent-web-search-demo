#!/usr/bin/env python3
"""Optional B02 HTTPX-only live HTML smoke test, separate from offline acceptance."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from local_search_demo.fetch.httpx_fetcher import (
    HTMLFetcher, create_http_client, save_html,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URLS = [
    "https://example.org/",
    "https://docs.python.org/3/library/asyncio.html",
]


async def probe(urls: list[str], *, timeout: float, max_bytes: int, save: bool) -> dict:
    rows = []
    async with create_http_client(trust_env=True) as client:
        fetcher = HTMLFetcher(client)
        for index, url in enumerate(urls, start=1):
            document = await fetcher.fetch(url, timeout=timeout, max_bytes=max_bytes)
            digest = sha256(document.html_bytes).hexdigest() if document.html_bytes is not None else None
            if save and document.result.status == "PASS":
                save_html(document, ROOT / "reports/B02/raw" / f"page_{index}.html")
            rows.append({
                "requested_url": url,
                "result": document.result.model_dump(mode="json"),
                "html_sha256": digest,
                "preview": (document.html[:160] if document.html is not None else None),
            })
    return {
        "batch": "B02",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "explicit_live_smoke",
        "status": "LIVE_PASS" if any(r["result"]["status"] == "PASS" for r in rows) else "LIVE_BLOCKED",
        "rows": rows,
        "note": "Optional live connectivity/HTML observations; does not assess article-extraction quality.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", action="append", dest="urls", help="May repeat; otherwise use default public test URLs")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)
    parser.add_argument("--save-html", action="store_true", help="Write already-fetched bytes to ignored reports/B02/raw")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/B02/live-smoke.json")
    args = parser.parse_args()
    result = asyncio.run(probe(
        args.urls or DEFAULT_URLS, timeout=args.timeout, max_bytes=args.max_bytes, save=args.save_html,
    ))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "statuses": [row["result"]["status"] for row in result["rows"]],
        "output": str(args.output),
    }, ensure_ascii=False))
    return 0 if result["status"] == "LIVE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
