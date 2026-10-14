"""B06 compatibility API using the single public-only network policy."""
from __future__ import annotations

import asyncio
import ipaddress
import socket
import httpx

from local_search_demo.fetch.public_network import (
    PublicURLTransport, Resolver, URLPolicyError, create_public_http_client,
    is_public_address, validate_public_url,
)


class UnsafeDestination(URLPolicyError):
    pass


def validate_url(url: httpx.URL) -> tuple[str, int]:
    try:
        checked = validate_public_url(str(url))
    except URLPolicyError as exc:
        raise UnsafeDestination(str(exc), kind=exc.kind) from exc
    return checked.raw_host.decode("ascii").rstrip("."), 443 if checked.scheme == "https" else 80


async def resolve_public(hostname: str, port: int) -> list[str]:
    """Resolve once and reject any disallowed IPv4/IPv6 answer."""
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            rows = await asyncio.to_thread(socket.getaddrinfo, hostname, port, type=socket.SOCK_STREAM)
        except (OSError, UnicodeError) as exc:
            raise UnsafeDestination("DNS resolution failed", kind="DNS_ERROR") from exc
        addresses = list(dict.fromkeys(row[4][0] for row in rows))
    else:
        addresses = [str(literal)]
    if not addresses or any(not is_public_address(ip) for ip in addresses):
        raise UnsafeDestination("All DNS answers must be allowed public addresses")
    return [str(ipaddress.ip_address(ip)) for ip in addresses]


class SafePublicTransport(PublicURLTransport):
    """Keep the B06 upstream/resolver injection API for trusted QA callers."""
    def __init__(self, *, resolver: Resolver = resolve_public,
                 upstream: httpx.AsyncBaseTransport | None = None):
        super().__init__(resolver=resolver, delegate=upstream)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        try:
            return await super().handle_async_request(request)
        except URLPolicyError as exc:
            raise UnsafeDestination(str(exc), kind=exc.kind) from exc


def create_safe_agent_client(*, transport: PublicURLTransport | None = None) -> httpx.AsyncClient:
    return create_public_http_client(transport=transport if transport is not None else SafePublicTransport())
