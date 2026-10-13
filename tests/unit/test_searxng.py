"""Offline SearXNG search adapter regression using HTTPX MockTransport."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from local_search_demo.schemas import SearchResult
from local_search_demo.search.searxng import SearXNGClient, search_web

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "search"


def _client(response, status=200):
    def handle(request: httpx.Request) -> httpx.Response:
        if isinstance(response, Exception):
            raise response
        return httpx.Response(
            status_code=status,
            json=response if isinstance(response, dict) else None,
            text=response if isinstance(response, str) else None,
            request=request,
        )
    return httpx.AsyncClient(transport=httpx.MockTransport(handle))


@pytest.mark.asyncio
async def test_success_parameters_and_first_ranking():
    data = json.loads((FIXTURE / "success.json").read_text())
    seen = []

    def reply(request):
        seen.append(request)
        return httpx.Response(200, json=data)

    async with httpx.AsyncClient(transport=httpx.MockTransport(reply)) as client:
        result = await SearXNGClient("http://127.0.0.1:8080/", client).search(
            "local demo", limit=5, language="zh-CN", time_range="week",
        )
    assert result.status == "PASS"
    assert result.http_status == 200
    assert len(result.items) == 2
    assert result.items[0].rank == 1
    assert result.items[1].rank == 2
    assert seen[0].url.path == "/search"
    assert seen[0].url.params["q"] == "local demo"
    assert seen[0].url.params["format"] == "json"
    assert seen[0].url.params["language"] == "zh-CN"
    assert seen[0].url.params["time_range"] == "week"


@pytest.mark.asyncio
async def test_duplicate_urls_are_merged():
    data = json.loads((FIXTURE / "duplicate_urls.json").read_text())
    async with _client(data) as client:
        result = await SearXNGClient("http://localhost:8080", client).search("duplicates")
    assert result.status == "PASS"
    assert len(result.items) == 1
    assert result.items[0].title == "First"
    assert result.items[0].engines == ["fixture-a", "fixture-b"]


@pytest.mark.asyncio
async def test_missing_fields_are_preserved_without_invention():
    data = json.loads((FIXTURE / "missing_fields.json").read_text())
    async with _client(data) as client:
        result = await SearXNGClient("http://localhost:8080", client).search("missing")
    assert result.status == "PASS"
    assert len(result.items) == 1
    assert result.items[0].title is None


@pytest.mark.asyncio
async def test_no_results_is_empty_not_success():
    data = json.loads((FIXTURE / "empty.json").read_text())
    async with _client(data) as client:
        result = await SearXNGClient("http://localhost:8080", client).search("none")
    assert result.status == "EMPTY"
    assert result.items == []
    assert result.http_status == 200


@pytest.mark.asyncio
async def test_upstream_failure_with_no_results():
    data = {"results": [], "unresponsive_engines": [["bing", "timeout"]]}
    async with _client(data) as client:
        result = await SearXNGClient("http://localhost:8080", client).search("query")
    assert result.status == "UPSTREAM_BLOCKED"
    assert result.errors[0].kind == "UPSTREAM_UNRESPONSIVE"


@pytest.mark.asyncio
@pytest.mark.parametrize("status,kind", [
    (403, "JSON_FORBIDDEN"),
    (429, "RATE_LIMITED"),
    (503, "HTTP_ERROR"),
])
async def test_http_errors(status, kind):
    async with _client({"error": "failed"}, status) as client:
        result = await SearXNGClient("http://localhost:8080", client).search("query")
    assert result.status == "FAIL"
    assert result.http_status == status
    assert result.errors[0].kind == kind


@pytest.mark.asyncio
async def test_invalid_json_and_response_shape():
    async with _client("not-json") as client:
        result = await SearXNGClient("http://localhost:8080", client).search("query")
    assert result.errors[0].kind == "INVALID_JSON"
    async with _client({"results": None}) as client:
        result = await SearXNGClient("http://localhost:8080", client).search("query")
    assert result.errors[0].kind == "INVALID_RESPONSE"


@pytest.mark.asyncio
async def test_timeout_and_transport_error():
    async with _client(httpx.ReadTimeout("slow server")) as client:
        r = await SearXNGClient("http://localhost:8080", client).search("query")
    assert r.errors[0].kind == "TIMEOUT"
    async with _client(httpx.ConnectError("unavailable")) as client:
        r = await SearXNGClient("http://localhost:8080", client).search("query")
    assert r.errors[0].kind == "NETWORK_ERROR"


@pytest.mark.asyncio
async def test_input_validation_avoids_network():
    def unreachable(request):
        raise AssertionError("should never request remote SearXNG")
    async with httpx.AsyncClient(transport=httpx.MockTransport(unreachable)) as client:
        adapter = SearXNGClient("http://localhost:8080", client)
        for kwargs in ({"query": ""}, {"query": "x", "limit": 0},
                       {"query": "x", "time_range": "minute"}):
            assert (await adapter.search(**kwargs)).status == "FAIL"


@pytest.mark.asyncio
async def test_convenience_api_uses_injected_client():
    async with _client({"results": [{"url": "https://example.org"}]}) as client:
        result = await search_web("test", base_url="http://localhost:8080", client=client)
    assert result.status == "PASS"
    assert isinstance(result, SearchResult)


def test_cli_writes_experiment_json(monkeypatch, tmp_path, capsys):
    from local_search_demo.interfaces import cli

    async def stub(query, **kwargs):
        return SearchResult(status="PASS", items=[], elapsed_ms=2.5, http_status=200)

    monkeypatch.setattr(cli, "search_web", stub)
    target = tmp_path / "search.json"
    assert cli.main(["search", "fixture", "--json", "--output", str(target)]) == 0
    record = json.loads(target.read_text())
    stdout = json.loads(capsys.readouterr().out)
    assert stdout["mode"] == "search"
    assert record["query"] == "fixture"
    assert record["total_elapsed_ms"] == 2.5


@pytest.mark.parametrize("error_kind,expected", [
    ("NETWORK_ERROR", "BLOCKED_LOCAL"),
    ("TIMEOUT", "BLOCKED_LOCAL"),
    ("JSON_FORBIDDEN", "CONFIG_ERROR"),
    ("INVALID_RESPONSE", "CONFIG_ERROR"),
    ("UPSTREAM_UNRESPONSIVE", "UPSTREAM_BLOCKED"),
])
def test_live_smoke_classifies_failures(error_kind, expected):
    from runpy import run_path
    script = Path(__file__).resolve().parents[2] / "scripts/b01-live-smoke.py"
    classify = run_path(str(script))["classify_live"]
    attempts = [{
        "has_valid_results": False,
        "result": {"status": "FAIL", "items": [], "errors": [
            {"kind": error_kind, "message": "simulated"}]},
    }]
    assert classify(attempts) == expected
    attempts[0]["has_valid_results"] = True
    assert classify(attempts) == "LIVE_PASS"
