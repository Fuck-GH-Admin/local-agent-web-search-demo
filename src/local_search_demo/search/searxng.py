"""SearXNG HTTP JSON search adapter, independent from webpage reading or LLMs."""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

import httpx

from local_search_demo.schemas import ErrorDetail, SearchItem, SearchResult


def _error(kind: str, message: str) -> ErrorDetail:
    return ErrorDetail(kind=kind, message=message[:400])


def _engines(row: dict[str, Any]) -> list[str]:
    candidates = row.get("engines")
    if isinstance(candidates, list):
        result = [v.strip() for v in candidates if isinstance(v, str) and v.strip()]
        if result:
            return list(dict.fromkeys(result))
    engine = row.get("engine")
    return [engine.strip()] if isinstance(engine, str) and engine.strip() else []


def _upstream_errors(value: Any) -> list[ErrorDetail]:
    errors = []
    if not isinstance(value, list):
        return errors
    for row in value:
        if isinstance(row, (list, tuple)) and row:
            name = str(row[0])
            reason = str(row[1]) if len(row) > 1 else "unresponsive"
        elif isinstance(row, dict):
            name = str(row.get("name") or row.get("engine") or "unknown")
            reason = str(row.get("error") or row.get("reason") or "unresponsive")
        else:
            name, reason = str(row), "unresponsive"
        errors.append(_error("UPSTREAM_UNRESPONSIVE", f"{name}: {reason}"))
    return errors


def normalize_results(data: Any, limit: int) -> tuple[list[SearchItem], list[ErrorDetail]]:
    """Normalize SearXNG's JSON response; keep first-seen ranking, merge engines.

    Malformed and non-http URLs are rejected; empty is not treated as success.
    """
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ValueError("SearXNG JSON response must contain a results array")
    errors = _upstream_errors(data.get("unresponsive_engines"))
    dedup: dict[str, SearchItem] = {}
    for row in data["results"]:
        if not isinstance(row, dict):
            continue
        url = row.get("url")
        if not isinstance(url, str):
            continue
        url = url.strip()
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                continue
        except ValueError:
            continue
        engines = _engines(row)
        if url in dedup:
            item = dedup[url]
            item.engines = list(dict.fromkeys([*item.engines, *engines]))
            continue
        if len(dedup) >= limit:
            continue
        title = row.get("title")
        snippet = row.get("content")
        dedup[url] = SearchItem(
            url=url,
            title=title if isinstance(title, str) else None,
            snippet=snippet if isinstance(snippet, str) else None,
            engines=engines,
            rank=len(dedup) + 1,
        )
    return list(dedup.values()), errors


class SearXNGClient:
    """Inject httpx.AsyncClient for pooling and deterministic MockTransport tests."""

    def __init__(self, base_url: str, client: httpx.AsyncClient):
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        self.base_url = base_url.rstrip("/")
        self.client = client

    async def search(
        self,
        query: str,
        limit: int = 10,
        language: str | None = None,
        time_range: str | None = None,
        timeout: float = 10.0,
    ) -> SearchResult:
        if not query.strip():
            return SearchResult(status="FAIL", errors=[_error("INVALID_QUERY", "Search query is empty")])
        if not 1 <= limit <= 30:
            return SearchResult(status="FAIL", errors=[_error("INVALID_LIMIT", "limit must be between 1 and 30")])
        if time_range and time_range not in ("day", "week", "month", "year"):
            return SearchResult(status="FAIL", errors=[_error("INVALID_TIME_RANGE", "expected day/week/month/year")])
        params: dict[str, str | int] = {
            "q": query.strip(), "format": "json",
        }
        if language:
            params["language"] = language
        if time_range:
            params["time_range"] = time_range

        started = time.perf_counter()
        response: httpx.Response | None = None
        try:
            response = await self.client.get(
                f"{self.base_url}/search", params=params, timeout=timeout,
                follow_redirects=True,
            )
            if response.status_code == 403:
                return self._failed("JSON_FORBIDDEN", "HTTP 403: enable json in search.formats", started, 403)
            if response.status_code == 429:
                return self._failed("RATE_LIMITED", "HTTP 429: SearXNG request rejected", started, 429)
            if response.status_code >= 400:
                return self._failed("HTTP_ERROR", f"HTTP {response.status_code} from SearXNG", started, response.status_code)
            try:
                payload = response.json()
            except ValueError:
                return self._failed("INVALID_JSON", "SearXNG did not return valid JSON", started, response.status_code)
            try:
                items, errors = normalize_results(payload, limit)
            except ValueError as exc:
                return self._failed("INVALID_RESPONSE", str(exc), started, response.status_code)
            return SearchResult(
                status="PASS" if items else ("UPSTREAM_BLOCKED" if errors else "EMPTY"),
                items=items,
                errors=errors,
                elapsed_ms=self._ms(started),
                http_status=response.status_code,
            )
        except httpx.TimeoutException:
            return self._failed("TIMEOUT", "SearXNG request timed out", started)
        except httpx.RequestError as exc:
            return self._failed("NETWORK_ERROR", type(exc).__name__, started)

    @staticmethod
    def _ms(started: float) -> float:
        return round((time.perf_counter() - started) * 1000, 3)

    @classmethod
    def _failed(
        cls, kind: str, message: str, started: float, http_status: int | None = None
    ) -> SearchResult:
        return SearchResult(
            status="FAIL",
            errors=[_error(kind, message)],
            elapsed_ms=cls._ms(started),
            http_status=http_status,
        )


async def search_web(
    query: str,
    *,
    base_url: str = "http://127.0.0.1:8080",
    limit: int = 10,
    language: str | None = None,
    time_range: str | None = None,
    timeout: float = 10.0,
    client: httpx.AsyncClient | None = None,
) -> SearchResult:
    """Convenience entrypoint; caller can pass a long-lived shared HTTPX client."""
    if client is not None:
        return await SearXNGClient(base_url, client).search(
            query, limit=limit, language=language, time_range=time_range, timeout=timeout
        )
    async with httpx.AsyncClient() as owned_client:
        return await SearXNGClient(base_url, owned_client).search(
            query, limit=limit, language=language, time_range=time_range, timeout=timeout
        )
