"""B07 ordinary API / CLI shared Agent service verification; no paid provider calls."""
from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from local_search_demo.agent.provider import (
    AssistantTurn, RequestedTool, ScriptedModelProvider,
)
from local_search_demo.agent.service import (
    AgentConfigurationError, execute_agent, live_read_gate,
)
from local_search_demo.web.api import create_app


URL = "https://docs.python.org/3/library/asyncio.html"


def tool(call_id, name, args):
    return RequestedTool(call_id, name, json.dumps(args))


def provider():
    return ScriptedModelProvider([
        AssistantTurn(tool_calls=[
            tool("search-1", "search_web", {"query": "python asyncio"}),
        ]),
        AssistantTurn(tool_calls=[
            tool("read-2", "read_webpage", {"url": URL}),
        ]),
        AssistantTurn(content="See https://docs.python.org/3/library/asyncio.html"),
    ])


def html_response(request):
    if request.url.path == "/search":
        return httpx.Response(200, json={
            "results": [{"title": "Python asyncio", "url": URL,
                         "content": "Official documentation", "engine": "unit"}]
        })
    if request.url.path == "/3/library/asyncio.html":
        return httpx.Response(
            200,
            content=b"<html><article><h1>Asyncio</h1><p>B00_ARTICLE_CORE source.</p></article></html>",
            headers={"Content-Type": "text/html"},
        )
    raise AssertionError("Unexpected URL " + str(request.url))


def test_shared_service_reads_original_core_offline():
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(html_response)) as client:
            return await execute_agent(
                "Find asyncio source", search_client=client, provider=provider(),
                searxng_base_url="http://searxng.test:8080",
            )
    result = asyncio.run(go())
    assert result.agent.status == "DONE"
    assert [c.call_id for c in result.agent.tool_calls] == ["search-1", "read-2"]
    assert [c.name for c in result.agent.tool_calls] == ["search_web", "read_webpage"]
    assert result.agent.cited_urls == [URL]
    assert "B00_ARTICLE_CORE" in result.agent.tool_calls[1].result["selected_text"]


def test_agent_api_reads_same_shared_core_and_renders_browser_html():
    observed = []

    def handler(request):
        observed.append(request.url.path)
        return html_response(request)

    app = create_app(
        client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        searxng_base_url="http://searxng.test:8080",
        agent_provider_factory=provider,
    )
    with TestClient(app) as client:
        page = client.get("/")
        js = client.get("/static/app.js")
        assert page.status_code == 200
        assert 'id="agent-form"' in page.text
        assert 'id="agent-live-read"' in page.text
        assert "renderAgent" in js.text
        assert ".innerHTML" not in js.text
        response = client.post("/api/agent", json={"question":"Find asyncio source"})
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "agent"
        assert data["agent"]["status"] == "DONE"
        assert data["agent"]["cited_urls"] == [URL]
        assert [t["call_id"] for t in data["agent"]["tool_calls"]] == ["search-1", "read-2"]
        assert observed == ["/search", "/3/library/asyncio.html"]


def test_cross_origin_agent_is_refused_before_model_invocation():
    calls = []

    def no_call():
        calls.append(True)
        return provider()

    app = create_app(
        client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(html_response)),
        agent_provider_factory=no_call,
    )
    with TestClient(app) as client:
        r = client.post("/api/agent", json={"question": "test"}, headers={
            "Origin": "https://malicious.invalid",
        })
        assert r.status_code == 403
        assert r.json()["status"] == "FORBIDDEN"
        assert calls == []


def test_api_live_read_needs_explicit_server_approval():
    app = create_app(
        client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(html_response)),
        agent_provider_factory=provider,
        agent_live_read_opt_in=False,
    )
    with TestClient(app) as client:
        denied = client.post("/api/agent", json={
            "question": "test", "allow_live_read": True,
        })
        assert denied.status_code == 403
        assert denied.json()["status"] == "LIVE_READ_DISABLED"


def test_invalid_api_budget_rejected_without_model_calls():
    created = []

    def factory():
        created.append(1)
        return provider()

    app = create_app(
        client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(html_response)),
        agent_provider_factory=factory,
    )
    with TestClient(app) as client:
        assert client.post("/api/agent", json={"question":"", "timeout":60}).status_code == 422
        assert client.post("/api/agent", json={"question":"x", "timeout":121}).status_code == 422
        assert client.post("/api/agent", json={"question":"x", "tool_choice":"secret"}).status_code == 422
        assert client.post("/api/agent", json={"question":"x", "api_key":"unexpected"}).status_code == 422
    assert created == []


def test_g6_gate_is_pass_from_accepted_main():
    permitted, reason = live_read_gate()
    assert permitted is True, reason


@pytest.mark.parametrize("kwargs", [
    {"timeout": 999}, {"max_rounds": 99}, {"max_tokens": 0},
])
def test_invalid_agent_budgets_fail_before_any_call(kwargs):
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(html_response)) as client:
            return await execute_agent("q",search_client=client,provider=provider(),**kwargs)
    with pytest.raises(AgentConfigurationError):
        asyncio.run(go())
