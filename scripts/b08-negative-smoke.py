#!/usr/bin/env python3
"""Controlled HTTP fault checks through the real read CLI, without public sites."""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread
import time

ROOT = Path(__file__).resolve().parents[1]


def run():
    hits = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            if self.path == "/slow":
                time.sleep(0.2)
            self.send_response({"/limited": 429, "/denied": 403}.get(self.path, 200))
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            try:
                self.wfile.write(b"<html><article>Controlled HTTP fault fixture</article></html>")
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    rows = []
    try:
        for endpoint, kind in [("/limited", "RATE_LIMITED"), ("/denied", "HTTP_ERROR"), ("/slow", "TIMEOUT")]:
            timeout = "0.05" if endpoint == "/slow" else "1"
            result = subprocess.run(
                [sys.executable, "-m", "local_search_demo", "read",
                 f"http://127.0.0.1:{server.server_port}{endpoint}",
                 "--timeout", timeout, "--json"],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            record = json.loads(result.stdout)
            fetch = record["fetch"]
            observed = (fetch.get("error") or {}).get("kind")
            statuses = [parser["status"] for parser in record["parsers"]]
            passed = (result.returncode == 1 and fetch["status"] == "FAIL"
                      and observed == kind and record["selected_text"] is None
                      and len(statuses) == 3 and all(s == "NOT_RUN" for s in statuses))
            rows.append({
                "case": endpoint, "expected_error": kind, "observed_error": observed,
                "http_status": fetch["http_status"], "fetch_status": fetch["status"],
                "exit_code": result.returncode, "parser_statuses": statuses,
                "elapsed_ms": record["total_elapsed_ms"], "pass": passed,
            })
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    passed = all(row["pass"] for row in rows) and hits == ["/limited", "/denied", "/slow"]
    return {
        "batch": "B08", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "kind": "controlled_loopback_HTTP_faults_real_CLI",
        "status": "PASS" if passed else "FAIL", "cases": rows, "actual_requests": hits,
        "real_public_fault_induced": False, "real_model_invoked": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/B08/validation/negative-http.json")
    args = parser.parse_args()
    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(report["cases"])}))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
