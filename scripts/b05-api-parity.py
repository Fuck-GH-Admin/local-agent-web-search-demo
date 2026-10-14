#!/usr/bin/env python3
"""B05 reproducible CLI/API parity using one synthetic localhost HTTP origin.

No SearXNG installation, credentials, browser automation or public network.
This is automated parity, not G3 human WebUI signoff.
"""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Thread
from typing import Any

from fastapi.testclient import TestClient

from local_search_demo.fetch.httpx_fetcher import create_http_client
from local_search_demo.web.api import create_app

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "tests/fixtures/html/static_article.html").read_bytes()
SPA = (ROOT / "tests/fixtures/html/spa_empty.html").read_bytes()
SEARCH = (ROOT / "tests/fixtures/search/success.json").read_bytes()


def canonical_read(record: dict[str, Any]) -> dict[str, Any]:
    """Remove clock/run ids and durations; keep all parser quality evidence."""
    return {
        "mode": record["mode"],
        "url": record["url"],
        "fetch": {
            key: record["fetch"][key] for key in [
                "status", "url_requested", "url_final", "http_status",
                "content_type", "bytes", "encoding", "redirect_history", "error",
            ]
        },
        "selected_parser": record["selected_parser"],
        "selected_text": record["selected_text"],
        "selection_reason": record["selection_reason"],
        "selection_evidence": [
            {k: v for k, v in item.items() if k not in ("elapsed_ms",)}
            for item in record["selection_evidence"]
        ],
        "parsers": [
            {k: v for k, v in parser.items() if k not in ("elapsed_ms",)}
            for parser in record["parsers"]
        ],
    }


def canonical_search(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": record["mode"],
        "query": record["query"],
        "search": {k: v for k, v in record["search"].items() if k != "elapsed_ms"},
    }


def run() -> tuple[dict, int]:
    hits = {"/article": 0, "/spa": 0, "/missing": 0, "/search": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            key = self.path.split("?", 1)[0]
            if key in hits:
                hits[key] += 1
            if key == "/article":
                data, status, ctype = HTML, 200, "text/html; charset=utf-8"
            elif key == "/spa":
                data, status, ctype = SPA, 200, "text/html; charset=utf-8"
            elif key == "/search":
                data, status, ctype = SEARCH, 200, "application/json"
            else:
                data, status, ctype = b"<html>not found</html>", 404, "text/html"
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    env = os.environ.copy()
    env["SEARXNG_BASE_URL"] = base
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = env["NO_PROXY"]
    scenarios: list[dict] = []

    def cli(*args: str) -> dict:
        process = subprocess.run(
            [sys.executable, "-m", "local_search_demo", *args, "--json"],
            cwd=ROOT, env=env, text=True, capture_output=True, timeout=30,
        )
        if not process.stdout.strip():
            raise RuntimeError(f"CLI had no JSON: {process.stderr[-400:]}")
        return {"exit": process.returncode, "data": json.loads(process.stdout)}

    try:
        app = create_app(
            searxng_base_url=base,
            client_factory=lambda: create_http_client(trust_env=False),
        )
        with TestClient(app) as api:
            for path in ("/article", "/spa", "/missing"):
                url = base + path
                from_cli = cli("read", url)
                from_api = api.post("/api/read", json={"url": url})
                same = canonical_read(from_cli["data"]) == canonical_read(from_api.json())
                expected_exit = 0 if path == "/article" else 1
                scenarios.append({
                    "scenario": path,
                    "cli_exit": from_cli["exit"],
                    "api_http": from_api.status_code,
                    "matching_core_fields": same,
                    "pass": same and from_api.status_code == 200 and from_cli["exit"] == expected_exit,
                    "chosen_parser": from_api.json()["selected_parser"],
                    "parser_status": [p["status"] for p in from_api.json()["parsers"]],
                })
            query = "local demo"
            from_cli = cli("search", query, "--limit", "5")
            from_api = api.post("/api/search", json={"query": query, "limit": 5})
            same = canonical_search(from_cli["data"]) == canonical_search(from_api.json())
            scenarios.append({
                "scenario": "/search",
                "cli_exit": from_cli["exit"],
                "api_http": from_api.status_code,
                "matching_core_fields": same,
                "pass": same and from_api.status_code == 200 and from_cli["exit"] == 0,
                "search_results": len(from_api.json()["search"]["items"]),
            })
            health = api.get("/health")
            agent = api.post("/api/agent", json={"question": "test"})
            webui = api.get("/")
            scenarios.append({
                "scenario": "http_routes",
                "pass": (health.status_code == 200 and agent.status_code == 501
                         and webui.status_code == 200 and 'id="panel-read"' in webui.text),
            })
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

    report = {
        "batch": "B05",
        "kind": "offline_CLI_API_core_parity",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(x["pass"] for x in scenarios)
                  and hits == {"/article": 2, "/spa": 2, "/missing": 2, "/search": 2}
                  else "FAIL",
        "scenarios": scenarios,
        "origin_request_counts": hits,
        "excluded_dynamic_fields": [
            "run_id", "timestamp", "total_elapsed_ms", "search.elapsed_ms",
            "fetch.elapsed_ms", "parsers[].elapsed_ms",
        ],
        "quality_scope": "Same synthetic HTML and JSON search fixtures for CLI/API; real browser rendering and human G3 acceptance NOT_RUN",
    }
    return report, 0 if report["status"] == "PASS" else 2


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "reports/B05/api-tests.json")
    args = parser.parse_args()
    report, code = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "batch": "B05", "status": report["status"],
        "scenarios": len(report["scenarios"]),
        "output": str(args.output),
    }, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
