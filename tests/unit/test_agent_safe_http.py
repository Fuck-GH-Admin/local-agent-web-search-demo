"""B06 security tests: DNS pinning, redirects, proxies, and Agent live dispatcher.

All transport traffic is mock; no public connection needed. These tests assert
the actual socket TARGET is the vetted IP, not merely a checked hostname.
"""
from __future__ import annotations

import asyncio
import httpx
import pytest

from local_search_demo.agent.safe_http import (
    SafePublicTransport, UnsafeDestination, create_safe_agent_client,
    validate_url, resolve_public,
)
from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.agent import dispatcher as module


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/", "http://0x7f000001/", "http://localhost/",
    "http://sub.localhost/", "http://[::1]/", "http://169.254.169.254/latest",
    "http://192.168.1.1/", "http://10.1.2.3/",
    "http://172.16.2.2/", "http://[fc00::1]/", "http://[fe80::1]/",
    "http://user:pass@www.example.org/", "ftp://www.example.org/",
    "http://www.example.org:2222/", "http://metadata.internal/",
    "https://[::ffff:127.0.0.1]/",
])
def test_unsafe_syntax_or_dns_cannot_bypass_filter(url):
    with pytest.raises(UnsafeDestination):
        validate_url(httpx.URL(url))


@pytest.mark.asyncio
async def test_resolver_rejects_dns_private_or_mixed_public_private(monkeypatch):
    def fake(host, port, **kwargs):
        if host == "mix.example.org":
            return [(2, 1, 6, "", ("93.184.215.14", port)), (2, 1, 6, "", ("127.0.0.1", port))]
        return [(2, 1, 6, "", ("192.168.0.44", port))]
    import socket
    monkeypatch.setattr(socket, "getaddrinfo", fake)
    for name in ("mix.example.org", "only-private.example.org"):
        with pytest.raises(UnsafeDestination):
            await resolve_public(name, 443)


@pytest.mark.asyncio
async def test_pinned_socket_target_retains_original_https_host_and_sni():
    observations = []
    async def resolve(host, port):
        observations.append(("dns", host, port))
        return ["93.184.215.14"]
    def handler(req):
        observations.append(("connect", str(req.url), req.headers.get("host"), req.extensions.get("sni_hostname")))
        return httpx.Response(200, text="<article>Safe document</article>", headers={"Content-Type":"text/html"})
    t = SafePublicTransport(resolver=resolve, upstream=httpx.MockTransport(handler))
    async with create_safe_agent_client(transport=t) as client:
        response = await client.get("https://www.example.org/story")
    assert response.status_code == 200
    assert response.url == httpx.URL("https://www.example.org/story")
    assert observations == [
        ("dns", "www.example.org", 443),
        ("connect", "https://93.184.215.14/story", "www.example.org", "www.example.org"),
    ]


@pytest.mark.asyncio
async def test_each_redirect_is_resolved_and_rejects_internal_target():
    observations = []
    async def resolve(host, port):
        observations.append(("dns", host))
        if host == "private.example.org":
            return ["10.0.0.4"]
        return ["93.184.215.14"]

    def handler(req):
        observations.append(("connect", req.url.host))
        return httpx.Response(302, headers={"Location": "http://private.example.org/internal"})

    t = SafePublicTransport(resolver=resolve, upstream=httpx.MockTransport(handler))
    async with create_safe_agent_client(transport=t) as client:
        with pytest.raises(UnsafeDestination):
            await client.get("https://www.example.org/start")
    assert observations == [
        ("dns", "www.example.org"), ("connect", "93.184.215.14"),
        ("dns", "private.example.org"),
    ]


@pytest.mark.asyncio
async def test_legitimate_relative_and_external_public_redirects_are_pinned():
    captured = []
    async def resolver(host, port):
        captured.append(("dns", host))
        return ["93.184.215.14"] if host == "www.example.org" else ["8.8.8.8"]
    def handler(req):
        captured.append(("request", str(req.url)))
        if req.url.path == "/start":
            return httpx.Response(302, headers={"Location": "/intermediate"})
        if req.url.path == "/intermediate":
            return httpx.Response(302, headers={"Location": "https://elsewhere.example.org/final"})
        return httpx.Response(200, text="<html>final</html>")
    t = SafePublicTransport(resolver=resolver, upstream=httpx.MockTransport(handler))
    async with create_safe_agent_client(transport=t) as client:
        r = await client.get("https://www.example.org/start")
    assert r.status_code == 200
    assert str(r.url) == "https://elsewhere.example.org/final"
    assert [str(x.url) for x in r.history] == [
        "https://www.example.org/start", "https://www.example.org/intermediate",
    ]
    assert captured == [
        ("dns","www.example.org"),("request","https://93.184.215.14/start"),
        ("dns","www.example.org"),("request","https://93.184.215.14/intermediate"),
        ("dns","elsewhere.example.org"),("request","https://8.8.8.8/final"),
    ]


@pytest.mark.asyncio
async def test_dns_rebinding_is_not_resolved_twice_within_single_hop():
    calls = []
    async def resolver(host,port):
        calls.append(host)
        return ["93.184.215.14"] if len(calls) == 1 else ["127.0.0.1"]
    hits = []
    t = SafePublicTransport(
        resolver=resolver,
        upstream=httpx.MockTransport(lambda req: (
            hits.append(req.url.host) or httpx.Response(200, text="<p>safe</p>")
        )),
    )
    async with create_safe_agent_client(transport=t) as client:
        await client.get("https://www.example.org/read")
    assert calls == ["www.example.org"]
    assert hits == ["93.184.215.14"]


@pytest.mark.asyncio
async def test_redirect_limit_stops_loop():
    count = 0
    async def resolver(host, port):
        return ["93.184.215.14"]
    def handler(req):
        nonlocal count
        count += 1
        return httpx.Response(302, headers={"Location":"/same"})
    t = SafePublicTransport(resolver=resolver,upstream=httpx.MockTransport(handler))
    async with create_safe_agent_client(transport=t) as client:
        with pytest.raises(httpx.TooManyRedirects):
            await client.get("https://www.example.org/same")
    assert count == 6


@pytest.mark.asyncio
async def test_dangerous_proxy_env_is_ignored(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:8888")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:8888")
    async def resolver(host,port):
        return ["93.184.215.14"]
    hosts = []
    t = SafePublicTransport(
        resolver=resolver,
        upstream=httpx.MockTransport(lambda req: (hosts.append(req.url.host) or httpx.Response(200,text="ok"))),
    )
    async with create_safe_agent_client(transport=t) as c:
        r=await c.get("https://www.example.org/story")
    assert r.status_code == 200
    assert hosts == ["93.184.215.14"]


@pytest.mark.asyncio
async def test_live_agent_uses_pinned_transport_without_local_search_client_leak(monkeypatch):
    article = b"<article><h1>Safe document</h1><p>Readable evidence.</p></article>"
    hits = []
    async def resolver(host,port):
        return ["93.184.215.14"]
    pinned_transport = SafePublicTransport(
        resolver=resolver,
        upstream=httpx.MockTransport(lambda req: (
            hits.append((req.url.host,req.headers.get("host"))) or
            httpx.Response(200,content=article,headers={"Content-Type":"text/html"})
        ))
    )
    monkeypatch.setattr(module,"create_safe_agent_client",lambda: create_safe_agent_client(transport=pinned_transport))
    searxng_calls = []
    def local_search(req):
        searxng_calls.append(req.url.path)
        return httpx.Response(200,json={"results":[{"url":"https://www.example.org/story","title":"Safe"}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(local_search)) as local:
        tools = AgentToolDispatcher(client=local,mode="live",enable_live_reads=True)
        search = await tools.execute("search_web",{"query":"public document"})
        fetched = await tools.execute("read_webpage",{"url":"https://www.example.org/story"})
    assert search["status"] == "PASS"
    assert fetched["status"] == "PASS"
    assert fetched["selected_text"]
    assert searxng_calls == ["/search"]
    assert hits == [("93.184.215.14","www.example.org")]
