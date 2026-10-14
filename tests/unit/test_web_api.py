"""B05 FastAPI tests; no real external web requests."""
from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from local_search_demo.web.api import create_app

ROOT = Path(__file__).resolve().parents[1]
ARTICLE = (ROOT / "fixtures/html/static_article.html").read_bytes()
SPA = (ROOT / "fixtures/html/spa_empty.html").read_bytes()


@pytest.fixture
def fixture_client():
    seen = []

    def reply(request):
        seen.append((request.method, request.url.path))
        if request.url.path == "/search":
            return httpx.Response(200, json={
                "query": "test query",
                "results": [
                    {"url": "https://example.org/a", "title": "<script>alert(1)</script>",
                     "content": "research summary", "engine": "demo"},
                    {"url": "https://example.org/b", "title": "Source B", "content": "second",
                     "engines": ["demo", "other"]},
                ],
            })
        if request.url.path == "/article":
            return httpx.Response(200, content=ARTICLE, headers={"Content-Type": "text/html"})
        if request.url.path == "/spa":
            return httpx.Response(200, content=SPA, headers={"Content-Type": "text/html"})
        return httpx.Response(404, text="Not found")

    def factory():
        return httpx.AsyncClient(transport=httpx.MockTransport(reply))

    app = create_app(client_factory=factory, searxng_base_url="http://searxng.test:8080")
    with TestClient(app) as client:
        yield client, seen


def test_webui_assets_and_health(fixture_client):
    client, seen = fixture_client
    home = client.get("/")
    assert home.status_code == 200
    assert 'id="panel-search"' in home.text
    assert 'id="panel-read"' in home.text
    assert 'id="panel-agent"' in home.text
    assert 'role="tablist"' in home.text
    css = client.get("/static/app.css")
    js = client.get("/static/app.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert "textContent" in js.text
    assert ".innerHTML" not in js.text
    assert client.get("/health").json() == {
        "status": "ok", "app": "local-search-demo", "phase": "B05",
        "search_engine_checked": False,
    }
    assert seen == []


def test_search_endpoint_uses_b01_core_and_keeps_titles_as_data(fixture_client):
    client, seen = fixture_client
    r = client.post("/api/search", json={"query": "test query", "limit": 5, "language": "zh-CN"})
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "search"
    assert data["search"]["status"] == "PASS"
    assert len(data["search"]["items"]) == 2
    assert data["search"]["items"][0]["title"] == "<script>alert(1)</script>"
    assert seen == [("GET", "/search")]


def test_empty_query_does_not_hit_searxng(fixture_client):
    client, seen = fixture_client
    data = client.post("/api/search", json={"query": ""}).json()
    assert data["search"]["status"] == "FAIL"
    assert data["search"]["errors"][0]["kind"] == "INVALID_QUERY"
    assert seen == []


def test_read_endpoint_gets_exactly_one_html_and_three_parsers(fixture_client):
    client, seen = fixture_client
    r = client.post("/api/read", json={"url": "http://testserver/article"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "read"
    assert body["fetch"]["status"] == "PASS"
    assert body["fetch"]["http_status"] == 200
    assert body["selected_parser"] is not None
    assert "B00_ARTICLE_CORE" in body["selected_text"]
    assert len(body["parsers"]) == 3
    assert len(body["selection_evidence"]) == 3
    assert seen == [("GET", "/article")]


def test_read_missing_or_spa_never_fakes_success(fixture_client):
    client, seen = fixture_client
    empty = client.post("/api/read", json={"url": "http://testserver/spa"}).json()
    assert empty["fetch"]["status"] == "PASS"
    assert empty["selected_parser"] is None
    assert all(x["status"] == "EMPTY" for x in empty["parsers"])
    missing = client.post("/api/read", json={"url": "http://testserver/missing"}).json()
    assert missing["fetch"]["status"] == "FAIL"
    assert missing["selected_text"] is None
    assert all(x["status"] == "NOT_RUN" for x in missing["parsers"])


def test_agent_is_explicit_501_and_not_executed(fixture_client):
    client, seen = fixture_client
    r = client.post("/api/agent", json={"question": "example"})
    assert r.status_code == 501
    assert r.json()["status"] == "NOT_IMPLEMENTED"
    assert seen == []


def test_schema_rejects_extra_fields_and_bad_json(fixture_client):
    client, seen = fixture_client
    assert client.post("/api/read", json={"url": "https://example.org", "api_key": "test"}).status_code == 422
    assert client.post("/api/search", json={"query": "test", "unknown": 1}).status_code == 422
    assert client.post("/api/search", content="{bad", headers={"Content-Type": "application/json"}).status_code == 422
    assert seen == []


def test_api_searxng_upstream_error_retains_core_status(fixture_client):
    client, seen = fixture_client
    response = client.post("/api/search", json={"query": "test query", "limit": 0})
    assert response.status_code == 200
    assert response.json()["search"]["errors"][0]["kind"] == "INVALID_LIMIT"
    assert seen == []



def test_loopback_host_guard_and_browser_safety_headers(fixture_client):
    client, seen = fixture_client
    ok = client.get("/")
    assert ok.status_code == 200
    assert ok.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in ok.headers["content-security-policy"]
    assert ok.headers["x-content-type-options"] == "nosniff"
    rejected = client.get("/", headers={"Host": "attacker.example"})
    assert rejected.status_code == 400
    assert seen == []
