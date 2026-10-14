#!/usr/bin/env python3
"""B04 repeatable offline CLI smoke: real loopback HTTP, no external sites."""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/html"


def run() -> tuple[dict, int]:
    sources = {
        "/article": (FIXTURES / "static_article.html").read_bytes(),
        "/spa": (FIXTURES / "spa_empty.html").read_bytes(),
    }
    hit_count = {key: 0 for key in sources}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in sources:
                hit_count[self.path] += 1
                data, status = sources[self.path], 200
            else:
                data, status = b"<html>not found</html>", 404
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thr = Thread(target=srv.serve_forever, daemon=True)
    thr.start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    items = []
    try:
        for path, expected_code in (("/article", 0), ("/spa", 1), ("/missing", 1)):
            command = [
                sys.executable, "-m", "local_search_demo", "read",
                url + path, "--json",
            ]
            outcome = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
            record = json.loads(outcome.stdout)
            passed = outcome.returncode == expected_code
            if path == "/article":
                passed &= record["fetch"]["http_status"] == 200
                passed &= record["selected_parser"] is not None
                passed &= "B00_ARTICLE_CORE" in (record["selected_text"] or "")
            elif path == "/spa":
                passed &= record["selected_parser"] is None
                passed &= all(r["status"] == "EMPTY" for r in record["parsers"])
            else:
                passed &= record["fetch"]["http_status"] == 404
                passed &= all(r["status"] == "NOT_RUN" for r in record["parsers"])
            items.append({
                "scenario": path,
                "exit_code": outcome.returncode,
                "expected_exit_code": expected_code,
                "pass": bool(passed),
                "experiment": record,
            })
    finally:
        srv.shutdown()
        srv.server_close()
        thr.join(timeout=3)
    report = {
        "batch": "B04",
        "kind": "offline_real_CLI_loopback_HTTP",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(i["pass"] for i in items) and hit_count == {
            "/article": 1, "/spa": 1,
        } else "FAIL",
        "server_requests": hit_count,
        "scenarios": items,
        "warning": "No real public website, model call, WebUI or article-quality human review is asserted.",
    }
    return report, 0 if report["status"] == "PASS" else 2


def main() -> int:
    target = ROOT / "reports/B04/cli-smoke.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    data, exit_code = run()
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "batch": "B04", "status": data["status"],
        "scenarios": len(data["scenarios"]),
        "file": str(target),
    }, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
