"""Pinned public-IP transport for model-controlled webpage fetches.

Prevents DNS rebinding/redirect SSRF by resolving each requested hostname once,
rejecting any private or special IP, and connecting to that validated IP while
preserving the requested hostname as Host and TLS certificate/SNI identity.

Only for untrusted Agent reads. User-operated B04 CLI retains its own semantics.
Network proxy settings are intentionally disabled; never silently route via proxy.
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable

import httpx

Resolver = Callable[[str, int], Awaitable[list[str]]]


class UnsafeDestination(ValueError):
    pass


def validate_url(url: httpx.URL) -> tuple[str, int]:
    if url.scheme not in ("http", "https") or not url.host:
        raise UnsafeDestination("Only absolute HTTP(S) URLs are permitted")
    if url.username or url.password:
        raise UnsafeDestination("Credentials inside a URL are prohibited")
    if url.port not in (None, 80 if url.scheme == "http" else 443):
        raise UnsafeDestination("Nonstandard ports are prohibited")
    hostname = url.host.rstrip(".").lower()
    if not hostname or "%" in hostname or "\\" in hostname:
        raise UnsafeDestination("Invalid hostname")
    if any(hostname == d or hostname.endswith("." + d) for d in (
        "localhost", "localdomain", "local", "internal", "test", "invalid",
        "example", "onion", "home.arpa"
    )):
        raise UnsafeDestination("Local/special-use hostname prohibited")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        if "." not in hostname or len(hostname) > 253 or any(not label or len(label) > 63 for label in hostname.split(".")):
            raise UnsafeDestination("Invalid public DNS hostname")
    else:
        if not address.is_global or getattr(address, "ipv4_mapped", None):
            raise UnsafeDestination("Non-global IP literal")
    return hostname, 443 if url.scheme == "https" else 80


async def resolve_public(hostname: str, port: int) -> list[str]:
    """Resolve once; all returned A/AAAA addresses must be public."""
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            rows = await asyncio.to_thread(
                socket.getaddrinfo, hostname, port, type=socket.SOCK_STREAM
            )
        except (OSError, UnicodeError) as exc:
            raise UnsafeDestination("DNS resolution failed") from exc
        addresses = list(dict.fromkeys(row[4][0] for row in rows))
    else:
        addresses = [str(literal)]
    if not addresses:
        raise UnsafeDestination("DNS returned no addresses")
    try:
        parsed = [ipaddress.ip_address(ip) for ip in addresses]
    except ValueError as exc:
        raise UnsafeDestination("DNS returned malformed address") from exc
    if any(not ip.is_global or getattr(ip, "ipv4_mapped", None) for ip in parsed):
        raise UnsafeDestination("DNS returned non-global address")
    return [str(ip) for ip in parsed]


class SafePublicTransport(httpx.AsyncBaseTransport):
    """Per-hop validation and IP pinning; the outer HTTPX client owns redirects."""

    def __init__(
        self, *,
        resolver: Resolver = resolve_public,
        upstream: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._resolver = resolver
        # Direct transport: no env/system proxy and no alternate name lookup.
        self._upstream = upstream or httpx.AsyncHTTPTransport(
            verify=True, http2=False, retries=0,
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        # Executed for initial request AND each redirect, even if it references
        # a literal IP. Reject before the underlying transport makes a socket.
        host, port = validate_url(request.url)
        ips = await self._resolver(host, port)
        if not ips:
            raise UnsafeDestination("DNS returned no usable addresses")
        canonical: list[str] = []
        try:
            for value in ips:
                addr = ipaddress.ip_address(value)
                if not addr.is_global or getattr(addr, "ipv4_mapped", None):
                    raise UnsafeDestination("DNS returned non-global IP")
                canonical.append(str(addr))
        except ValueError as exc:
            raise UnsafeDestination("DNS returned invalid IP") from exc
        # Pin the CONNECT TARGET IP. No second lookup of the hostname is
        # performed by HTTPX; TLS still validates the original public hostname.
        ip = canonical[0]
        new_url = request.url.copy_with(host=ip)
        hdrs = httpx.Headers(request.headers)
        hdrs["Host"] = host if request.url.port is None else f"{host}:{port}"
        pinned = httpx.Request(
            method=request.method,
            url=new_url,
            headers=hdrs,
            stream=request.stream,
            extensions={**request.extensions, "sni_hostname": host},
        )
        result = await self._upstream.handle_async_request(pinned)
        # Let the outer HTTPX client associate original URL with the returned
        # response so history and relative redirect targets remain correct.
        return httpx.Response(
            status_code=result.status_code, headers=result.headers,
            stream=result.stream, extensions=result.extensions,
        )

    async def aclose(self) -> None:
        await self._upstream.aclose()


def create_safe_agent_client(*, transport: SafePublicTransport | None = None) -> httpx.AsyncClient:
    """For untrusted Agent read ONLY. No system proxies or env certificate overrides."""
    return httpx.AsyncClient(
        transport=transport or SafePublicTransport(),
        trust_env=False, follow_redirects=True, max_redirects=5,
        timeout=httpx.Timeout(8.0),
        headers={"User-Agent": "LocalAgentWebSearchDemo/0.1"},
    )
