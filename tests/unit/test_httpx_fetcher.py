"""B02 offline HTTPX fetch unit tests (no public network)."""
from __future__ import annotations

import gzip

import httpx
import pytest

from local_search_demo.fetch.httpx_fetcher import (
    HTMLFetcher, create_http_client, decode_html, save_html,
)


def mock_client(handler, *, max_redirects=5):
    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler), max_redirects=max_redirects
    )


@pytest.mark.asyncio
async def test_html_bytes_and_metadata(tmp_path):
    data = "<html><body><p>测试 HTML byte-identical</p></body></html>".encode("utf-8")
    async with mock_client(lambda req: httpx.Response(
        200, content=data, headers={"Content-Type": "text/html; charset=utf-8"}
    )) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/article")
    assert doc.result.status == "PASS"
    assert doc.html_bytes == data
    assert "测试 HTML" in doc.html
    assert doc.result.bytes == len(data)
    assert doc.result.url_final == "https://example.org/article"
    assert doc.result.http_status == 200
    assert doc.result.encoding.lower() == "utf-8"
    assert doc.result.elapsed_ms >= 0
    assert doc.result.redirect_history == []
    path = tmp_path / "raw" / "page.html"
    save_html(doc, path)
    assert path.read_bytes() == data
    assert doc.result.html_path == str(path)


@pytest.mark.asyncio
async def test_redirect_preserves_original_and_final_url():
    def handler(request):
        if request.url.path == "/start":
            return httpx.Response(302, headers={"Location": "/end"})
        return httpx.Response(200, text="<article>Done</article>", headers={"Content-Type": "text/html"})
    async with mock_client(handler) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/start")
    assert doc.result.status == "PASS"
    assert doc.result.url_requested.endswith("/start")
    assert doc.result.url_final.endswith("/end")
    assert doc.result.redirect_history == ["https://example.org/start"]


@pytest.mark.asyncio
@pytest.mark.parametrize("status,kind", [(404,"HTTP_ERROR"),(429,"RATE_LIMITED"),(503,"HTTP_ERROR")])
async def test_http_failures_return_no_content(status, kind):
    async with mock_client(lambda request: httpx.Response(status, text="<html>error</html>")) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/bad")
    assert doc.result.status == "FAIL"
    assert doc.result.http_status == status
    assert doc.result.error.kind == kind
    assert doc.html is None and doc.html_bytes is None


@pytest.mark.asyncio
async def test_unsupported_type_does_not_read_document():
    async with mock_client(lambda request: httpx.Response(
        200, content=b"%PDF-synthetic", headers={"Content-Type": "application/pdf"}
    )) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/file.pdf")
    assert doc.result.error.kind == "UNSUPPORTED_CONTENT_TYPE"
    assert doc.result.status == "FAIL"
    assert doc.html_bytes is None


@pytest.mark.asyncio
async def test_header_declared_large_rejected_early():
    async with mock_client(lambda req: httpx.Response(
        200, content=b"123456", headers={"Content-Type":"text/html","Content-Length":"6"}
    )) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/large", max_bytes=5)
    assert doc.result.error.kind == "TOO_LARGE"


@pytest.mark.asyncio
async def test_streaming_max_bytes_rejected_when_content_length_absent():
    async with mock_client(lambda req: httpx.Response(
        200, content=b"abcdefg", headers={"Content-Type": "text/html"}
    )) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/large", max_bytes=5)
    assert doc.result.error.kind == "TOO_LARGE"
    assert doc.html_bytes is None


@pytest.mark.asyncio
async def test_gzip_decoded_limit_applies_after_decompression():
    html = b"<html>" + b"x" * 2048 + b"</html>"
    compressed = gzip.compress(html)
    async with mock_client(lambda req: httpx.Response(
        200, content=compressed, headers={
            "Content-Encoding": "gzip", "Content-Type": "text/html",
            "Content-Length": str(len(compressed)),
        }
    )) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/gzip", max_bytes=256)
    assert doc.result.error.kind == "TOO_LARGE"


@pytest.mark.asyncio
async def test_timeout_and_network_failures_are_distinct():
    async with mock_client(lambda req: (_ for _ in ()).throw(httpx.ReadTimeout("slow"))) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/slow")
    assert doc.result.error.kind == "TIMEOUT"
    async with mock_client(lambda req: (_ for _ in ()).throw(httpx.ConnectError("offline"))) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/offline")
    assert doc.result.error.kind == "NETWORK_ERROR"


@pytest.mark.asyncio
async def test_redirect_loop_is_classified():
    async with mock_client(lambda req: httpx.Response(302, headers={"Location":"/loop"}), max_redirects=2) as client:
        doc = await HTMLFetcher(client).fetch("https://example.org/loop")
    assert doc.result.error.kind == "TOO_MANY_REDIRECTS"


@pytest.mark.asyncio
async def test_invalid_inputs_skip_network():
    def handler(_):
        raise AssertionError("must not touch network")
    async with mock_client(handler) as client:
        f = HTMLFetcher(client)
        for url in ["", "file:///etc/passwd", "javascript:alert(1)", "not-url"]:
            doc = await f.fetch(url)
            assert doc.result.error.kind == "INVALID_URL"
        for options in ({"max_bytes": 0}, {"timeout": 0}):
            doc = await f.fetch("https://example.org", **options)
            assert doc.result.error.kind == "INVALID_OPTIONS"


def test_meta_charset_when_header_missing():
    original = '<html><head><meta charset="gb18030"></head><body>中文编码</body></html>'
    data = original.encode("gb18030")
    decoded, encoding = decode_html(data, "text/html")
    assert decoded == original
    assert encoding == "gb18030"


def test_charset_declared_in_header_takes_precedence():
    data = "中文".encode("gb18030")
    decoded, encoding = decode_html(data, "text/html; charset=gb18030")
    assert decoded == "中文"
    assert encoding == "gb18030"


def test_missing_charset_falls_back_utf8():
    decoded, encoding = decode_html("文本".encode("utf-8"), None)
    assert decoded == "文本"
    assert encoding == "utf-8"


def test_save_rejects_failed_fetch(tmp_path):
    from local_search_demo.fetch.httpx_fetcher import FetchedHTML
    from local_search_demo.schemas import FetchResult
    with pytest.raises(ValueError):
        save_html(FetchedHTML(result=FetchResult(status="FAIL")), tmp_path/"wrong.html")


def test_factory_supplies_reusable_async_client():
    client = create_http_client(trust_env=False)
    try:
        assert isinstance(client, httpx.AsyncClient)
        assert client.max_redirects == 5
    finally:
        import asyncio
        asyncio.run(client.aclose())
