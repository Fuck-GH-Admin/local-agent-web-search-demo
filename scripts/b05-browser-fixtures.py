#!/usr/bin/env python3
"""Loopback-only saved HTML controls for real-browser G3 acceptance."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--counts", type=Path, default=ROOT / "reports/B05/fixture-hits.json")
    args = parser.parse_args()
    hits, lock = {}, Lock()
    fixtures = {"/article": "static_article.html", "/technical": "technical_documentation.html",
                "/spa": "spa_empty.html"}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/stats":
                with lock:
                    body = json.dumps(hits).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
                return
            with lock:
                hits[path] = hits.get(path, 0) + 1
                args.counts.parent.mkdir(parents=True, exist_ok=True)
                args.counts.write_text(json.dumps(hits, indent=2) + "\n")
            if path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/article")
                self.end_headers()
                return
            if path in fixtures:
                status, body = 200, (ROOT / "tests/fixtures/html" / fixtures[path]).read_bytes()
            else:
                status, body = 404, b"<html><body>G3 missing fixture</body></html>"
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"G3 saved fixture origin: http://127.0.0.1:{args.port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
