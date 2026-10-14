"""B06 offline scripted model -> actual B01 search/B04 read against MockTransport."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.agent.provider import AssistantTurn, RequestedTool, ScriptedModelProvider, OpenAIChatProvider
from local_search_demo.agent.runner import AgentRunner
from local_search_demo.agent.toolspec import TOOL_SCHEMAS

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures"


def script_tool(call_id: str, name: str, args: str | dict) -> RequestedTool:
    return RequestedTool(call_id, name, args if isinstance(args, str) else json.dumps(args))


@pytest.fixture
def http_client():
    hits = []
    search_data = json.loads((FIXTURE / "search/success.json").read_text())
    article = (FIXTURE / "html/static_article.html").read_bytes()

    def reply(request):
        hits.append(request.url.path)
        if request.url.path == "/search":
            return httpx.Response(200, json=search_data)
        if request.url.path == "/article":
            return httpx.Response(200, content=article, headers={"Content-Type": "text/html"})
        return httpx.Response(404, text="not found")

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    yield client, hits
    asyncio.run(client.aclose())


def runner_for(http_client, turns, **kwargs):
    client, _ = http_client
    provider = ScriptedModelProvider(turns)
    dispatcher = AgentToolDispatcher(client=client, searxng_base_url="http://searxng.local",mode="offline_fixture")
    return AgentRunner(provider, dispatcher, **kwargs), provider


@pytest.mark.asyncio
async def test_no_tool_answer_is_zero_calls(http_client):
    runner, provider = runner_for(http_client, [AssistantTurn("7")])
    record = await runner.run("What is 3+4?")
    assert record.agent.status == "DONE"
    assert record.agent.answer == "7"
    assert record.agent.tool_calls == []
    assert provider.tool_choices == ["auto"]
    assert http_client[1] == []


@pytest.mark.asyncio
async def test_one_search_and_id_roundtrip(http_client):
    runner, provider = runner_for(http_client, [
        AssistantTurn(tool_calls=[script_tool("search_1","search_web",{"query":"test","limit":5})]),
        AssistantTurn("Found two results."),
    ])
    record = await runner.run("find search results")
    assert record.agent.status == "DONE"
    assert len(record.agent.tool_calls) == 1
    call = record.agent.tool_calls[0]
    assert (call.call_id,call.name,call.status) == ("search_1","search_web","PASS")
    assert len(call.result["items"]) == 2
    assert provider.received_messages[1][-1]["tool_call_id"] == "search_1"
    assert http_client[1] == ["/search"]


@pytest.mark.asyncio
async def test_search_then_read_has_actual_parsed_text(http_client):
    url = "https://example.org/article"
    runner, provider = runner_for(http_client, [
        AssistantTurn(tool_calls=[script_tool("s1", "search_web", {"query":"test"})]),
        AssistantTurn(tool_calls=[script_tool("r1", "read_webpage", {"url":url})]),
        AssistantTurn(f"The article says this: {url}"),
    ])
    record = await runner.run("find and read a page")
    assert record.agent.status == "DONE"
    assert http_client[1] == ["/search", "/article"]
    assert [x.call_id for x in record.agent.tool_calls] == ["s1","r1"]
    assert record.agent.tool_calls[1].result["selected_parser"] is not None
    assert "B00_ARTICLE_CORE" in record.agent.tool_calls[1].result["selected_text"]
    assert record.agent.cited_urls == [url]
    assert record.agent.unverified_citations == []
    assert provider.received_messages[2][-1]["tool_call_id"] == "r1"


@pytest.mark.asyncio
async def test_multiple_tools_in_one_assistant_message(http_client):
    runner, provider = runner_for(http_client, [
        AssistantTurn(tool_calls=[
            script_tool("a","search_web",{"query":"test"}),
            script_tool("b","search_web",{"query":"another"}),
        ]),
        AssistantTurn("searched twice"),
    ])
    record = await runner.run("search two topics")
    assert record.agent.status == "DONE"
    assert len(record.agent.tool_calls) == 2
    assert [x.call_id for x in record.agent.tool_calls] == ["a","b"]
    assert http_client[1] == ["/search","/search"]
    ids = [m["tool_call_id"] for m in provider.received_messages[1] if m["role"]=="tool"]
    assert ids == ["a","b"]


@pytest.mark.asyncio
async def test_bad_json_is_error_then_model_can_recover(http_client):
    runner, provider = runner_for(http_client, [
        AssistantTurn(tool_calls=[script_tool("bad","search_web","{oops")]),
        AssistantTurn("I can't search that."),
    ])
    record = await runner.run("search")
    assert record.agent.status == "DONE"
    assert record.agent.tool_calls[0].error.kind == "INVALID_JSON"
    assert provider.received_messages[1][-1]["tool_call_id"] == "bad"
    assert http_client[1] == []


@pytest.mark.asyncio
async def test_unknown_tool_is_bounded_error(http_client):
    runner, _ = runner_for(http_client,[
        AssistantTurn(tool_calls=[script_tool("hack","run_shell",{"command":"ls"})]),
        AssistantTurn("Cannot run shell."),
    ])
    record = await runner.run("run commands")
    assert record.agent.status == "DONE"
    assert record.agent.tool_calls[0].error.kind == "UNKNOWN_TOOL"
    assert http_client[1] == []


@pytest.mark.asyncio
async def test_unsourced_url_is_denied_before_any_fetch(http_client):
    url = "https://example.org/article"
    runner, _ = runner_for(http_client,[
        AssistantTurn(tool_calls=[script_tool("r1","read_webpage",{"url":url})]),
        AssistantTurn("Not permitted"),
    ])
    record = await runner.run("read unsourced URL")
    assert record.agent.tool_calls[0].error.kind == "URL_DENIED"
    assert http_client[1] == []


@pytest.mark.asyncio
async def test_search_provenance_is_reset_between_agent_runs(http_client):
    runner, provider = runner_for(http_client, [
        AssistantTurn(tool_calls=[script_tool("s", "search_web", {"query": "test"})]),
        AssistantTurn("search complete"),
        AssistantTurn(tool_calls=[script_tool("r", "read_webpage", {"url": "https://example.org/article"})]),
        AssistantTurn("refused"),
    ])
    first = await runner.run("search")
    second = await runner.run("read previous run's URL")
    assert first.agent.tool_calls[0].status == "PASS"
    assert second.agent.tool_calls[0].error.kind == "URL_DENIED"
    assert http_client[1] == ["/search"]


@pytest.mark.asyncio
@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "http://localhost:8000/", "http://127.0.0.1/",
    "http://192.168.1.1/", "http://169.254.169.254/latest/meta-data/",
    "https://user:pass@example.org/article",
    "https://example.org:444/article",
    "http://[::1]/", "http://example.org@localhost/",
])
async def test_private_and_invalid_url_never_fetch(http_client, url):
    runner,_ = runner_for(http_client,[
        AssistantTurn(tool_calls=[script_tool("s1","search_web",{"query":"test"})]),
        AssistantTurn(tool_calls=[script_tool("r1","read_webpage",{"url":url})]),
        AssistantTurn("denied"),
    ])
    record = await runner.run("unsafe URL")
    assert record.agent.tool_calls[-1].error.kind == "URL_DENIED"
    assert http_client[1] == ["/search"]


@pytest.mark.asyncio
async def test_live_mode_agent_read_uses_dns_guard(http_client):
    from local_search_demo.fetch.public_network import PublicURLTransport
    client, hits = http_client
    provider = ScriptedModelProvider([
        AssistantTurn(tool_calls=[script_tool("s","search_web",{"query":"test"})]),
        AssistantTurn(tool_calls=[script_tool("r","read_webpage",{"url":"https://example.org/article"})]),
        AssistantTurn("read refused"),
    ])
    async def private_dns(host, port):
        return ["127.0.0.1"]
    guard = PublicURLTransport(resolver=private_dns, delegate=httpx.MockTransport(lambda r: pytest.fail("Forbidden request")))
    dispatcher = AgentToolDispatcher(client=client, searxng_base_url="http://searxng.local",mode="live", public_transport=guard)
    record = await AgentRunner(provider, dispatcher).run("search read")
    assert record.agent.tool_calls[-1].error.kind == "URL_DENIED"
    assert hits == ["/search"]


@pytest.mark.asyncio
async def test_tool_quota_and_round_limit_are_finite(http_client):
    runner,_ = runner_for(http_client, [
        AssistantTurn(tool_calls=[
            script_tool("a","search_web",{"query":"test"}),
            script_tool("b","search_web",{"query":"test"}),
        ]),
    ], max_tool_calls=1, max_rounds=2)
    record = await runner.run("infinite calls")
    assert record.agent.status == "TOOL_LIMIT"
    assert [t.call_id for t in record.agent.tool_calls] == ["a","b"]
    assert record.agent.tool_calls[1].error.kind == "TOOL_LIMIT"
    assert http_client[1] == ["/search"]
    runner,_ = runner_for(http_client, [
        AssistantTurn(tool_calls=[script_tool("a","search_web",{"query":"test"})]),
    ], max_rounds=1)
    r=await runner.run("no final answer")
    assert r.agent.status == "MAX_ROUNDS"
    assert r.agent.answer is None


@pytest.mark.asyncio
async def test_model_timeout_is_recorded_not_crashed(http_client):
    class SlowProvider(ScriptedModelProvider):
        async def complete(self, messages, *, tool_choice="auto"):
            await asyncio.sleep(0.1)
            return AssistantTurn("unreachable")
    r,_ = runner_for(http_client,[])
    r.provider=SlowProvider([])
    r.timeout=0.01
    outcome=await r.run("slow")
    assert outcome.agent.status == "TIMEOUT"
    assert outcome.agent.answer is None


@pytest.mark.asyncio
async def test_unverified_url_from_answer_is_not_cited(http_client):
    runner,_ = runner_for(http_client,[
        AssistantTurn(content="Made up https://not-from-tools.example.org/report"),
    ])
    record=await runner.run("question")
    assert record.agent.status == "UNVERIFIED_CITATION"
    assert not record.agent.cited_urls
    assert record.agent.unverified_citations == ["https://not-from-tools.example.org/report"]


def test_openai_provider_explicitly_rejects_unimplemented_api_mode():
    with pytest.raises(ValueError, match="UNSUPPORTED_API_MODE"):
        OpenAIChatProvider(model="test",base_url="https://api.example.org/v1",api_key="fake",api_mode="responses")


def test_tool_schemas_have_no_unrestricted_arguments():
    names = [x["function"]["name"] for x in TOOL_SCHEMAS]
    assert names == ["search_web", "read_webpage"]
    assert all(x["function"]["parameters"]["additionalProperties"] is False for x in TOOL_SCHEMAS)
