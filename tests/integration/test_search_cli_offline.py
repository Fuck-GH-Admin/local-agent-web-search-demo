"""B01 full CLI -> real localhost HTTP -> normalized SearXNG JSON, without internet."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
from threading import Thread
from urllib.parse import parse_qs, urlparse


def test_cli_search_against_local_synthetic_searxng():
    payload = (Path(__file__).resolve().parents[1] / "fixtures/search/success.json").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlparse(self.path)
            params = parse_qs(path.query)
            if path.path != "/search" or params.get("format") != ["json"]:
                self.send_error(400)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "local_search_demo", "search",
             "local demo", "--json", "--limit", "3",
             "--base-url", f"http://127.0.0.1:{server.server_address[1]}"],
            capture_output=True, text=True, timeout=10,
        )
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["mode"] == "search"
    assert data["search"]["status"] == "PASS"
    assert data["search"]["http_status"] == 200
    assert len(data["search"]["items"]) == 2
    assert data["search"]["items"][1]["title"] == "本地示例文档"
