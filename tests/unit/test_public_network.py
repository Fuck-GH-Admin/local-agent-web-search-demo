"""Security regressions observe transport requests, not only boolean URL checks."""
from __future__ import annotations

import asyncio
from pathlib import Path
import socket
import ssl

import httpcore
import httpx
import pytest

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.fetch.httpx_fetcher import HTMLFetcher
from local_search_demo.fetch.public_network import (
    PublicURLTransport, URLPolicyError, create_public_http_client, validate_public_url,
)
from local_search_demo.pipeline.reader import read_webpage

ARTICLE = (Path(__file__).resolve().parents[1] / "fixtures/html/static_article.html").read_bytes()
PUBLIC = "93.184.215.14"


async def public_dns(host, port):
    return [PUBLIC]


@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "ftp://example.org/", "gopher://example.org/",
    "http://localhost/", "http://LOCALHOST./", "http://x.localhost/",
    "http://printer.local/", "http://metadata.google.internal/",
    "http://localhost.localdomain/", "http://router.home.arpa/",
    "http://127.0.0.1/", "http://0.0.0.0/", "http://10.0.0.1/",
    "http://172.16.0.1/", "http://192.168.1.1/", "http://100.64.0.1/",
    "http://169.254.169.254/latest/meta-data/", "http://169.254.170.2/",
    "http://168.63.129.16/", "http://100.100.100.200/",
    "http://224.0.0.1/", "http://240.0.0.1/", "http://192.0.2.1/",
    "http://192.0.0.8/", "http://192.88.99.1/", "http://198.18.0.1/",
    "http://[::1]/", "http://[::]/", "http://[fe80::1]/",
    "http://[fc00::1]/", "http://[ff02::1]/", "http://[2001:db8::1]/",
    "http://[::ffff:127.0.0.1]/", "http://[::ffff:8.8.8.8]/",
    "http://[64:ff9b::7f00:1]/", "http://[64:ff9b:1::a00:1]/",
    "http://[2002:7f00:1::]/", "http://[2001::1]/", "http://[fe80::1%25eth0]/",
    "http://[fec0::1]/", "http://[3fff::1]/", "http://[2001:20::1]/",
    "http://2130706433/", "http://0177.0.0.1/", "http://127.1/",
    "http://0x7f000001/", "http://0x7f.0.0.1/", "http://127.000.000.001/",
    "http://%31%32%37.0.0.1/", "https://user:secret@example.org/",
    "https://@example.org/", "http://example.org@127.0.0.1/",
    "https://example.org:444/", "https://example.org:80/",
    "http://example.org:443/", "http://example.org:0/",
    "http://example.org:65536/", "http://example.org:abc/",
    "http://example.org\\@127.0.0.1/", " https://example.org/",
    "https://example.org/\n", "https://exam\tple.org/",
])
def test_unsafe_syntax_is_rejected(url):
    with pytest.raises(URLPolicyError):
        validate_public_url(url)


@pytest.mark.parametrize("url", [
    "https://example.org/", "http://example.org:80/article",
    "https://example.org:443/a?q=one#section", "https://example.org./",
    "https://8.8.8.8/", "https://[2606:4700:4700::1111]/",
    "https://例子.中国/article",
])
def test_public_syntax_can_proceed_to_dns_check(url):
    assert validate_public_url(url).scheme in ("http", "https")


@pytest.mark.asyncio
@pytest.mark.parametrize("addresses", [
    [], ["127.0.0.1"], ["10.0.0.1"], ["169.254.169.254"], ["100.64.0.1"],
    ["::1"], ["fe80::1"], ["fc00::1"], ["::ffff:127.0.0.1"],
    [PUBLIC, "127.0.0.1"], [PUBLIC, "fc00::1"], ["not-an-ip"],
    ["192.0.0.8"], ["fec0::1"], ["3fff::1"],
])
async def test_every_dns_answer_must_be_public_before_transport(addresses):
    hits = []
    async def resolver(host, port):
        return addresses
    transport = PublicURLTransport(resolver=resolver, delegate=httpx.MockTransport(lambda r: hits.append(r)))
    async with create_public_http_client(transport=transport) as client:
        result = await read_webpage("https://article.example.org/a", client=client)
    assert result.fetch.error.kind == "URL_DENIED"
    assert result.selected_text is None
    assert all(p.status == "NOT_RUN" for p in result.parsers)
    assert hits == []


@pytest.mark.asyncio
async def test_dns_failure_and_timeout_fail_without_a_request():
    hits = []
    async def failure(host, port):
        raise socket.gaierror("test NXDOMAIN")
    async def slow(host, port):
        await asyncio.sleep(0.1)
        return [PUBLIC]
    for resolver, expected in [(failure, "DNS_ERROR"), (slow, "TIMEOUT")]:
        transport = PublicURLTransport(resolver=resolver, delegate=httpx.MockTransport(lambda r: hits.append(r)))
        async with create_public_http_client(transport=transport) as client:
            doc = await HTMLFetcher(client).fetch("https://article.example.org/a", timeout=0.01)
        assert doc.result.error.kind == expected
    assert hits == []


@pytest.mark.asyncio
async def test_dns_rebinding_is_pinned_and_next_resolution_is_rechecked():
    calls, requests = [], []
    async def rebind(host, port):
        calls.append((host, port))
        return [PUBLIC] if len(calls) == 1 else ["127.0.0.1"]
    def reply(request):
        requests.append(request)
        return httpx.Response(200, content=ARTICLE, headers={"Content-Type": "text/html"})
    transport = PublicURLTransport(resolver=rebind, delegate=httpx.MockTransport(reply))
    async with create_public_http_client(transport=transport) as client:
        first = await read_webpage("https://article.example.org/a", client=client)
        second = await read_webpage("https://article.example.org/a", client=client)
    assert first.fetch.status == "PASS" and "B00_ARTICLE_CORE" in first.selected_text
    assert first.fetch.url_final == "https://article.example.org/a"
    assert second.fetch.error.kind == "URL_DENIED"
    assert len(requests) == 1 and len(calls) == 2
    assert requests[0].url.host == PUBLIC
    assert requests[0].headers["Host"] == "article.example.org"
    assert requests[0].extensions["sni_hostname"] == "article.example.org"


@pytest.mark.asyncio
@pytest.mark.parametrize("url,host,header", [
    ("https://8.8.8.8/a", "8.8.8.8", "8.8.8.8"),
    ("https://[2606:4700:4700::1111]/a", "2606:4700:4700::1111", "[2606:4700:4700::1111]"),
])
async def test_public_ip_literal_needs_no_dns_and_preserves_host(url, host, header):
    hits = []
    async def forbidden_dns(*args):
        pytest.fail("IP literals must not be sent to DNS")
    def reply(request):
        hits.append(request)
        return httpx.Response(200, content=ARTICLE, headers={"Content-Type": "text/html"})
    guard = PublicURLTransport(resolver=forbidden_dns, delegate=httpx.MockTransport(reply))
    async with create_public_http_client(transport=guard) as client:
        record = await read_webpage(url, client=client)
    assert record.fetch.status == "PASS"
    assert hits[0].url.host == host
    assert hits[0].headers["Host"] == header


@pytest.mark.asyncio
async def test_public_reader_rejects_non_get_method_before_dns():
    async def forbidden_dns(*args):
        pytest.fail("Method rejected before DNS")
    guard = PublicURLTransport(resolver=forbidden_dns)
    async with create_public_http_client(transport=guard) as client:
        with pytest.raises(URLPolicyError, match="GET only"):
            await client.post("https://example.org/a", content=b"unexpected")


@pytest.mark.asyncio
@pytest.mark.parametrize("target", [
    "http://127.0.0.1/secret", "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/", "http://2130706433/", "https://article.example.org:8443/",
    "https://credentials:secret@example.org/", "https://private.example.org/",
    "//localhost/secret", "file:///etc/passwd",
])
async def test_redirect_targets_are_checked_before_their_request(target):
    hits = []
    async def resolver(host, port):
        return ["10.0.0.1"] if host == "private.example.org" else [PUBLIC]
    def reply(request):
        hits.append(str(request.url))
        return httpx.Response(302, headers={"Location": target})
    transport = PublicURLTransport(resolver=resolver, delegate=httpx.MockTransport(reply))
    async with create_public_http_client(transport=transport) as client:
        record = await read_webpage("https://article.example.org/a", client=client)
    assert record.fetch.status == "FAIL"
    assert record.fetch.error.kind in ("URL_DENIED", "NETWORK_ERROR")
    assert len(hits) == 1
    assert not record.selected_text


@pytest.mark.asyncio
async def test_public_relative_redirect_and_loop_limit_are_preserved():
    hits = []
    def reply(request):
        hits.append(request.url.path)
        if request.url.path == "/a":
            return httpx.Response(302, headers={"Location": "/b"})
        if request.url.path == "/b":
            return httpx.Response(200, content=ARTICLE, headers={"Content-Type": "text/html"})
        return httpx.Response(302, headers={"Location": "/loop"})
    transport = PublicURLTransport(resolver=public_dns, delegate=httpx.MockTransport(reply))
    async with create_public_http_client(transport=transport) as client:
        doc = await HTMLFetcher(client).fetch("https://article.example.org/a")
        loop = await HTMLFetcher(client).fetch("https://article.example.org/loop")
    assert doc.result.status == "PASS"
    assert doc.result.url_final == "https://article.example.org/b"
    assert doc.result.redirect_history == ["https://article.example.org/a"]
    assert loop.result.error.kind == "TOO_MANY_REDIRECTS"
    assert hits == ["/a", "/b"] + ["/loop"] * 6


@pytest.mark.asyncio
async def test_same_hostname_redirect_rebinding_is_denied():
    resolutions, hits = [], []
    async def resolver(host, port):
        resolutions.append(host)
        return [PUBLIC] if len(resolutions) == 1 else ["169.254.169.254"]
    def reply(request):
        hits.append(request.url.path)
        return httpx.Response(302, headers={"Location": "/second"})
    transport = PublicURLTransport(resolver=resolver, delegate=httpx.MockTransport(reply))
    async with create_public_http_client(transport=transport) as client:
        doc = await HTMLFetcher(client).fetch("https://article.example.org/first")
    assert doc.result.error.kind == "URL_DENIED"
    assert hits == ["/first"]
    assert resolutions == ["article.example.org"] * 2


@pytest.mark.asyncio
async def test_actual_httpcore_connection_uses_pinned_ip_and_verified_hostname(monkeypatch):
    from httpcore._backends.auto import AutoBackend
    observed = {"tcp": [], "tls": [], "sent": b""}
    class Stream(httpcore.AsyncNetworkStream):
        def __init__(self):
            self.done = False
        async def read(self, max_bytes, timeout=None):
            if self.done:
                return b""
            self.done = True
            return b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 13\r\n\r\n<h1>safe</h1>\n"
        async def write(self, buffer, timeout=None):
            observed["sent"] += buffer
        async def aclose(self):
            pass
        async def start_tls(self, ssl_context, server_hostname=None, timeout=None):
            observed["tls"].append(server_hostname)
            assert ssl_context.verify_mode == ssl.CERT_REQUIRED
            assert ssl_context.check_hostname
            return self
        def get_extra_info(self, info):
            return None
    async def connect(self, host, port, timeout=None, local_address=None, socket_options=None):
        observed["tcp"].append((host, port))
        return Stream()
    monkeypatch.setattr(AutoBackend, "connect_tcp", connect)
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    transport = PublicURLTransport(resolver=public_dns)
    async with create_public_http_client(transport=transport) as client:
        response = await client.get("https://article.example.org/a")
        other = await client.get("https://other.example.org/b")
    assert response.status_code == 200
    assert other.status_code == 200
    assert observed["tcp"] == [(PUBLIC, 443), (PUBLIC, 443)]
    assert observed["tls"] == ["article.example.org", "other.example.org"]
    assert b"Host: article.example.org\r\n" in observed["sent"]
    assert b"Host: other.example.org\r\n" in observed["sent"]


@pytest.mark.asyncio
async def test_dispatcher_live_mode_uses_guard_not_search_client():
    search_hits, read_hits = [], []
    url = "https://article.example.org/a"
    def search(request):
        search_hits.append(str(request.url))
        return httpx.Response(200, json={"results": [{"url": url, "title": "Article"}]})
    def article(request):
        read_hits.append(str(request.url))
        return httpx.Response(200, content=ARTICLE, headers={"Content-Type": "text/html"})
    transport = PublicURLTransport(resolver=public_dns, delegate=httpx.MockTransport(article))
    async with httpx.AsyncClient(transport=httpx.MockTransport(search)) as search_client:
        dispatcher = AgentToolDispatcher(client=search_client, public_transport=transport, enable_live_reads=True)
        assert (await dispatcher.execute("read_webpage", {"url": url}))["error"]["kind"] == "URL_DENIED"
        assert (await dispatcher.execute("search_web", {"query": "article"}))["status"] == "PASS"
        output = await dispatcher.execute("read_webpage", {"url": url})
    assert output["status"] == "PASS" and "B00_ARTICLE_CORE" in output["selected_text"]
    assert len(search_hits) == len(read_hits) == 1
    assert search_hits[0].startswith("http://127.0.0.1:8080/search")
    assert read_hits[0] == f"https://{PUBLIC}/a"


def test_model_cannot_inject_unprotected_transport():
    with pytest.raises(TypeError):
        create_public_http_client(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
