"""Network boundary for model-controlled reads, separate from explicit CLI reads.

Validate every request (including every redirect), reject any non-public DNS
answer, then connect to a validated literal IP. Host and TLS SNI remain the
original hostname. No environment proxy can perform a second DNS resolution.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
import ipaddress
import re
import socket
from urllib.parse import urlsplit

import httpx

Resolver = Callable[[str, int], Awaitable[Sequence[str]]]
_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z", re.I)
_LOCAL_SUFFIXES = (".localhost", ".local", ".localdomain", ".internal", ".home.arpa")
_TRANSITION_NETWORKS = tuple(ipaddress.ip_network(n) for n in (
    "64:ff9b::/96", "64:ff9b:1::/48", "2002::/16", "2001::/23",
    "fec0::/10", "3fff::/20",
))
_SPECIAL_V4 = tuple(ipaddress.ip_network(n) for n in ("192.0.0.0/24", "192.88.99.0/24"))
_PLATFORM_SERVICE_IPS = {"168.63.129.16"}  # Azure platform virtual IP / WireServer


class URLPolicyError(httpx.RequestError):
    def __init__(self, message: str, *, kind: str = "URL_DENIED"):
        super().__init__(message)
        self.kind = kind


def is_public_address(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if (not address.is_global or address.is_multicast or address.is_reserved
            or str(address) in _PLATFORM_SERVICE_IPS):
        return False
    # Conservative special-purpose ranges avoid Python-version classification
    # differences (notably pre-3.13 is_global) and address-translation routes.
    if isinstance(address, ipaddress.IPv4Address) and any(address in net for net in _SPECIAL_V4):
        return False
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None or address.scope_id is not None:
            return False
        if any(address in net for net in _TRANSITION_NETWORKS):
            return False
    return True


def validate_public_url(url: str) -> httpx.URL:
    """Syntax only; a domain still needs DNS validation at each request."""
    if not isinstance(url, str) or len(url) > 8192 or not url:
        raise URLPolicyError("Expected a bounded absolute HTTP(S) URL")
    if "\\" in url or any(ord(c) <= 32 or ord(c) == 127 for c in url):
        raise URLPolicyError("Ambiguous URL whitespace/control/backslash rejected")
    try:
        parsed = httpx.URL(url)
    except (httpx.InvalidURL, ValueError) as exc:
        raise URLPolicyError("Malformed URL") from exc
    if parsed.scheme not in ("http", "https") or not parsed.host:
        raise URLPolicyError("Only absolute HTTP(S) URLs may be read")
    # raw userinfo also rejects an empty embedded username (https://@host/).
    if parsed.userinfo or "@" in urlsplit(url).netloc:
        raise URLPolicyError("Embedded URL credentials are forbidden")
    expected_port = 443 if parsed.scheme == "https" else 80
    if parsed.port not in (None, expected_port):
        raise URLPolicyError("Only the scheme's default web port is allowed")
    host = parsed.raw_host.decode("ascii").lower().rstrip(".")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        labels = host.split(".")
        if (host == "localhost" or host.endswith(_LOCAL_SUFFIXES)
                or len(labels) < 2 or len(host) > 253
                or any(not _LABEL.fullmatch(label) for label in labels)
                or not any(c.isalpha() for c in labels[-1])
                or all(label.isdecimal() or label.lower().startswith("0x") for label in labels)):
            raise URLPolicyError("Local, malformed or alternate numeric hostname rejected")
    else:
        if not is_public_address(host):
            raise URLPolicyError("IP literal is not an allowed public address")
    return parsed


async def resolve_addresses(host: str, port: int) -> Sequence[str]:
    answers = await asyncio.get_running_loop().getaddrinfo(
        host, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP,
    )
    return list(dict.fromkeys(item[4][0] for item in answers))


class PublicURLTransport(httpx.AsyncBaseTransport):
    """Guard the actual transport destination, not just the initial URL string.

    Resolver/delegate injection is for trusted test code, never tool arguments.
    Keepalive is disabled: pooling by rewritten IP could otherwise reuse a TLS
    connection belonging to a different virtual host on the same address.
    """

    def __init__(self, *, resolver: Resolver = resolve_addresses,
                 delegate: httpx.AsyncBaseTransport | None = None):
        self.resolver = resolver
        self.delegate = delegate if delegate is not None else httpx.AsyncHTTPTransport(
            trust_env=False, retries=0, http2=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=0),
        )
        self.audit: list[dict] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        event = {"url": str(request.url), "decision": "DENIED"}
        self.audit.append(event)
        try:
            original = validate_public_url(str(request.url))
            if request.method != "GET":
                raise URLPolicyError("Public reader permits GET only")
            host = original.raw_host.decode("ascii").rstrip(".")
            port = original.port or (443 if original.scheme == "https" else 80)
            try:
                literal = ipaddress.ip_address(host)
            except ValueError:
                connect_timeout = request.extensions.get("timeout", {}).get("connect")
                # DNS must not silently escape the request's connection budget.
                budget = min(connect_timeout if connect_timeout is not None else 8.0, 8.0)
                try:
                    addresses = list(await asyncio.wait_for(self.resolver(host, port), budget))
                except asyncio.TimeoutError as exc:
                    raise httpx.ConnectTimeout("DNS resolution exceeded connection budget", request=request) from exc
                except (OSError, ValueError) as exc:
                    raise URLPolicyError("DNS resolution failed", kind="DNS_ERROR") from exc
            else:
                addresses = [str(literal)]
            event.update(hostname=host, resolved_addresses=addresses, port=port)
            if not addresses or any(not is_public_address(ip) for ip in addresses):
                raise URLPolicyError("DNS answers must all be allowed public addresses")
            # Prefer IPv4 on hosts without IPv6 connectivity; no hostname retry.
            addresses.sort(key=lambda value: ipaddress.ip_address(value).version)
            pinned_ip = str(ipaddress.ip_address(addresses[0]))
            headers = request.headers.copy()
            headers["Host"] = original.netloc.decode("ascii")
            extensions = {"sni_hostname": host}
            if "timeout" in request.extensions:
                extensions["timeout"] = request.extensions["timeout"]
            pinned = httpx.Request(
                request.method, original.copy_with(host=pinned_ip),
                headers=headers, stream=request.stream, extensions=extensions,
            )
            event.update(decision="ALLOWED", pinned_ip=pinned_ip)
            return await self.delegate.handle_async_request(pinned)
        except URLPolicyError as exc:
            event.update(error_kind=exc.kind, reason=str(exc))
            raise

    async def aclose(self) -> None:
        await self.delegate.aclose()


def create_public_http_client(*, transport: PublicURLTransport | None = None) -> httpx.AsyncClient:
    """A dedicated client; caller's SearXNG proxy/mounts cannot bypass the guard."""
    if transport is not None and not isinstance(transport, PublicURLTransport):
        raise TypeError("Model reads require PublicURLTransport")
    return httpx.AsyncClient(
        transport=transport if transport is not None else PublicURLTransport(),
        trust_env=False, follow_redirects=True, max_redirects=5,
        timeout=httpx.Timeout(8.0),
        headers={"User-Agent": "LocalAgentWebSearchDemo/0.1 (+public-only model reader)"},
    )
