"""B04 complete reader and CLI integration, using only localhost/fixtures."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread

import httpx
import pytest

from local_search_demo.pipeline.reader import read_webpage
from local_search_demo.schemas import ExperimentRecord

HTML = (Path(__file__).resolve().parents[1] / "fixtures/html/static_article.html").read_bytes()


@pytest.mark.asyncio
async def test_pipeline_gets_html_once_and_retains_three_results(tmp_path):
    count = 0
    def handler(_):
        nonlocal count
        count += 1
        return httpx.Response(200, content=HTML, headers={"Content-Type": "text/html; charset=utf-8"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        target = tmp_path / "raw" / "capture.html"
        record = await read_webpage("https://example.org/article", client=client, save_raw=target)
    assert count == 1
    assert target.read_bytes() == HTML
    assert record.fetch.status == "PASS"
    assert record.fetch.html_path == str(target)
    assert len(record.parsers) == 3
    assert len(record.selection_evidence) == 3
    assert record.selected_parser is not None
    assert "B00_ARTICLE_CORE" in record.selected_text
    assert record.total_elapsed_ms >= record.fetch.elapsed_ms
    assert ExperimentRecord.model_validate_json(record.model_dump_json()) == record


@pytest.mark.asyncio
async def test_failed_fetch_keeps_parser_status_not_run():
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda _: httpx.Response(429, content=b"rate limit")
    )) as client:
        record = await read_webpage("https://example.org/notavailable", client=client)
    assert record.fetch.status == "FAIL"
    assert record.fetch.http_status == 429
    assert record.selected_parser is None
    assert record.selected_text is None
    assert all(p.status == "NOT_RUN" for p in record.parsers)


@pytest.mark.asyncio
async def test_spa_shell_does_not_invent_body():
    empty = (Path(__file__).resolve().parents[1] / "fixtures/html/spa_empty.html").read_bytes()
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, content=empty, headers={"Content-Type":"text/html"})
    )) as client:
        record = await read_webpage("https://example.org/spa", client=client)
    assert record.fetch.status == "PASS"
    assert record.selected_parser is None
    assert record.selected_text is None
    assert len(record.parsers) == 3
    assert all(p.status == "EMPTY" for p in record.parsers)


@pytest.fixture
def local_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/article":
                content, status = HTML, 200
            else:
                content, status = b"<html>not found</html>", 404
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        def log_message(self, fmt, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_real_cli_read_loopback_produces_same_json_contract(local_server, tmp_path):
    target = tmp_path / "record.json"
    raw = tmp_path / "source.html"
    cmd = [
        sys.executable, "-m", "local_search_demo",
        "read", f"{local_server}/article",
        "--json", "--output", str(target), "--save-html", str(raw),
    ]
    process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert process.returncode == 0, process.stderr
    stdout = json.loads(process.stdout)
    disk = json.loads(target.read_text(encoding="utf-8"))
    assert stdout == disk
    assert stdout["mode"] == "read"
    assert stdout["selected_parser"] is not None
    assert "B00_ARTICLE_CORE" in stdout["selected_text"]
    assert raw.read_bytes() == HTML
    assert all(p["name"] in {"trafilatura", "readability", "selectolax"} for p in stdout["parsers"])


def test_real_cli_read_failure_is_not_success(local_server):
    process = subprocess.run([
        sys.executable, "-m", "local_search_demo", "read",
        f"{local_server}/notfound", "--json",
    ],capture_output=True,text=True,timeout=30)
    assert process.returncode == 1
    info = json.loads(process.stdout)
    assert info["fetch"]["http_status"] == 404
    assert info["selected_parser"] is None
    assert all(p["status"] == "NOT_RUN" for p in info["parsers"])


def test_cli_read_invalid_url_has_structured_failure(tmp_path):
    cmd = [sys.executable, "-m", "local_search_demo", "read", "not-a-url", "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path,timeout=30)
    assert result.returncode == 1
    body = json.loads(result.stdout)
    assert body["fetch"]["error"]["kind"] == "INVALID_URL"
    assert body["selected_text"] is None
