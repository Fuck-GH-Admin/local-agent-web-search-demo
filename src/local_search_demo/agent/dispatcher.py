"""B06 dispatcher reuses B01/B04 Core; model-controlled real URL fetch is CLOSED.

Offline fixtures use an explicitly injected HTTPX MockTransport client. B07 may
open real URL fetching only after the tracked SSRF / DNS / redirect checks pass.
"""
from __future__ import annotations

from urllib.parse import urlsplit
import ipaddress

import httpx

from local_search_demo.pipeline.reader import read_webpage
from local_search_demo.search.searxng import search_web
from local_search_demo.agent.safe_http import UnsafeDestination, create_safe_agent_client


def _failure(kind: str, message: str) -> dict:
    return {"status": "FAIL", "error": {"kind": kind, "message": message[:240]}}


def _public_url_syntax(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        if parsed.port not in (None, 80, 443):
            return False
        hostname = parsed.hostname.rstrip(".").lower()
        if hostname in ("localhost", "localhost.localdomain") or hostname.endswith(".localhost"):
            return False
        if "." not in hostname:
            return False
        try:
            return ipaddress.ip_address(hostname).is_global
        except ValueError:
            return True
    except (ValueError, TypeError):
        return False


class AgentToolDispatcher:
    """All model tool operations route through these two actual Core functions.

    mode='offline_fixture' requires an explicitly provided MockTransport client.
    Live mode uses a separate direct-only, DNS-pinned HTTP transport that validates
    every redirect. The SearXNG client remains local and separate.
    """

    def __init__(
        self, *,
        client: httpx.AsyncClient,
        searxng_base_url: str = "http://127.0.0.1:8080",
        mode: str = "live",
    ):
        if mode not in ("live", "offline_fixture"):
            raise ValueError("Unsupported dispatcher mode")
        if mode == "offline_fixture" and not isinstance(client._transport, httpx.MockTransport):
            raise ValueError("Offline fixture mode requires explicit HTTPX MockTransport")
        self.client = client
        self.searxng_base_url = searxng_base_url
        self.mode = mode
        self.found_urls: set[str] = set()

    async def execute(self, name: str, arguments: dict) -> dict:
        if not isinstance(arguments, dict):
            return _failure("INVALID_ARGUMENTS", "Expected JSON object arguments")
        if name == "search_web":
            if set(arguments) - {"query", "limit"}:
                return _failure("INVALID_ARGUMENTS", "Unknown search_web arguments")
            query = arguments.get("query")
            limit = arguments.get("limit", 5)
            if not isinstance(query, str) or not query.strip() or type(limit) is not int or not 1 <= limit <= 10:
                return _failure("INVALID_ARGUMENTS", "query must be nonempty string; limit integer 1-10")
            result = await search_web(
                query, limit=limit, client=self.client,
                base_url=self.searxng_base_url,
            )
            if result.status == "PASS":
                self.found_urls.update(x.url for x in result.items)
            return {
                "status": result.status,
                "items": [x.model_dump(mode="json") for x in result.items],
                "errors": [x.model_dump(mode="json") for x in result.errors],
            }
        if name == "read_webpage":
            if set(arguments) != {"url"} or not isinstance(arguments.get("url"), str):
                return _failure("INVALID_ARGUMENTS", "read_webpage needs exactly one URL string")
            url = arguments["url"]
            if not _public_url_syntax(url) or url not in self.found_urls:
                return _failure("URL_DENIED", "Only public-looking URLs returned by this run's search may be read")
            try:
                if self.mode == "offline_fixture":
                    record = await read_webpage(url, client=self.client, max_bytes=1_000_000)
                else:
                    # The search client may access localhost SearXNG, but it is
                    # NEVER used for model-controlled page downloads.
                    async with create_safe_agent_client() as safe_client:
                        record = await read_webpage(
                            url, client=safe_client, max_bytes=1_000_000,
                        )
            except UnsafeDestination:
                return _failure("URL_DENIED", "Destination failed public-IP / redirect validation")
            return {
                "status": record.fetch.status if record.fetch else "NOT_RUN",
                "url": record.fetch.url_final if record.fetch else None,
                "http_status": record.fetch.http_status if record.fetch else None,
                "selected_parser": record.selected_parser,
                "selected_text": (record.selected_text or "")[:6000],
                "error": record.fetch.error.model_dump(mode="json") if record.fetch and record.fetch.error else None,
            }
        return _failure("UNKNOWN_TOOL", f"Unregistered tool {name}")
