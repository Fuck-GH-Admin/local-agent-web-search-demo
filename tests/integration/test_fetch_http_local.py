"""Real localhost HTTP server exercises B02 streaming, redirect, status and charset."""
from __future__ import annotations

import asyncio
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time

import pytest

from local_search_demo.fetch.httpx_fetcher import HTMLFetcher, create_http_client


@pytest.fixture
def test_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path
            if path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/zh")
                self.end_headers()
                return
            if path == "/zh":
                data = '<!doctype html><meta charset="gb18030"><p>真实本地中文</p>'.encode("gb18030")
                content_type = "text/html"
                code = 200
            elif path == "/gzip":
                data = gzip.compress(b"<p>" + b"x" * 4096 + b"</p>")
                content_type = "text/html"
                code = 200
            elif path == "/pdf":
                data = b"%PDF-1.7"
                content_type = "application/pdf"
                code = 200
            elif path == "/slow":
                time.sleep(0.15)
                data = b"<html>slow</html>"
                content_type = "text/html"
                code = 200
            elif path in ("/403", "/404", "/429", "/503"):
                data = b"<html>synthetic error page</html>"
                content_type = "text/html"
                code = int(path[1:])
            else:
                data = b""
                content_type = "text/html"
                code = 200
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            if path == "/gzip":
                self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, format, *args):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)


@pytest.mark.asyncio
async def test_real_loopback_fetch_reuses_one_client(test_server):
    async with create_http_client(trust_env=False) as client:
        fetcher = HTMLFetcher(client)
        zh = await fetcher.fetch(test_server + "/redirect")
        missing = await fetcher.fetch(test_server + "/404")
        non_html = await fetcher.fetch(test_server + "/pdf")
        empty = await fetcher.fetch(test_server + "/empty")
    assert zh.result.status == "PASS"
    assert "真实本地中文" in zh.html
    assert zh.result.encoding == "gb18030"
    assert zh.result.redirect_history == [test_server + "/redirect"]
    assert missing.result.http_status == 404
    assert missing.html_bytes is None
    assert non_html.result.error.kind == "UNSUPPORTED_CONTENT_TYPE"
    assert empty.result.status == "EMPTY"
    assert empty.result.error.kind == "EMPTY_BODY"


@pytest.mark.asyncio
async def test_real_loopback_decoded_gzip_limit(test_server):
    async with create_http_client(trust_env=False) as client:
        too_big = await HTMLFetcher(client).fetch(test_server + "/gzip", max_bytes=512)
    assert too_big.result.error.kind == "TOO_LARGE"


@pytest.mark.asyncio
async def test_real_loopback_read_timeout(test_server):
    async with create_http_client(trust_env=False) as client:
        doc = await HTMLFetcher(client).fetch(test_server + "/slow", timeout=0.02)
    assert doc.result.error.kind == "TIMEOUT"


@pytest.mark.asyncio
@pytest.mark.parametrize("status,kind", [(403, "HTTP_ERROR"), (429, "RATE_LIMITED"), (503, "HTTP_ERROR")])
async def test_real_loopback_http_errors_never_return_html(test_server, status, kind):
    async with create_http_client(trust_env=False) as client:
        document = await HTMLFetcher(client).fetch(f"{test_server}/{status}")
    assert document.result.status == "FAIL"
    assert document.result.http_status == status
    assert document.result.error.kind == kind
    assert document.html is None and document.html_bytes is None
