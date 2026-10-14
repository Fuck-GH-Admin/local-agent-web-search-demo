"""B06 dispatcher reuses B01/B04 Core with a public-only model read transport."""
from __future__ import annotations

import httpx

from local_search_demo.fetch.public_network import (
    PublicURLTransport, URLPolicyError, create_public_http_client, validate_public_url,
)
from local_search_demo.pipeline.reader import read_webpage
from local_search_demo.search.searxng import search_web


def _failure(kind: str, message: str) -> dict:
    return {"status": "FAIL", "error": {"kind": kind, "message": message[:240]}}


def _public_url_syntax(url: str) -> bool:
    try:
        validate_public_url(url)
        return True
    except URLPolicyError:
        return False


class AgentToolDispatcher:
    """All model tool operations route through these two actual Core functions.

    mode='offline_fixture' requires an explicitly provided MockTransport client.
    In mode='live', reads use a separate public-only DNS-pinned client. Search
    still uses the trusted local SearXNG client; model arguments cannot select
    that service URL or opt into offline fixtures.
    """

    def __init__(
        self, *,
        client: httpx.AsyncClient,
        searxng_base_url: str = "http://127.0.0.1:8080",
        mode: str = "live",
        public_transport: PublicURLTransport | None = None,
    ):
        if mode not in ("live", "offline_fixture"):
            raise ValueError("Unsupported dispatcher mode")
        if mode == "offline_fixture" and not isinstance(client._transport, httpx.MockTransport):
            raise ValueError("Offline fixture mode requires explicit HTTPX MockTransport")
        if public_transport is not None and not isinstance(public_transport, PublicURLTransport):
            raise TypeError("Live model reads require PublicURLTransport")
        self.client = client
        self.searxng_base_url = searxng_base_url
        self.mode = mode
        self.public_transport = public_transport
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
            if self.mode == "offline_fixture":
                record = await read_webpage(url, client=self.client, max_bytes=1_000_000)
            else:
                async with create_public_http_client(transport=self.public_transport) as public_client:
                    record = await read_webpage(url, client=public_client, max_bytes=1_000_000)
            return {
                "status": record.fetch.status if record.fetch else "NOT_RUN",
                "url": record.fetch.url_final if record.fetch else None,
                "http_status": record.fetch.http_status if record.fetch else None,
                "selected_parser": record.selected_parser,
                "selected_text": (record.selected_text or "")[:6000],
                "error": record.fetch.error.model_dump(mode="json") if record.fetch and record.fetch.error else None,
            }
        return _failure("UNKNOWN_TOOL", f"Unregistered tool {name}")
