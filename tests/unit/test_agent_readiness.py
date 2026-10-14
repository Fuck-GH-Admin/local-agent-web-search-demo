"""B06 acceptance gaps: termination and actual SDK wire protocol, all offline."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.agent.provider import AssistantTurn, OpenAIChatProvider, RequestedTool, ScriptedModelProvider
from local_search_demo.agent.runner import AgentRunner
from local_search_demo.agent.toolspec import TOOL_SCHEMAS

ARTICLE = (Path(__file__).resolve().parents[1] / "fixtures/html/static_article.html").read_bytes()
URL = "https://example.org/article"


def tool(identifier, name="search_web", args=None):
    return RequestedTool(identifier, name, json.dumps(args or {"query": "test"}))


@pytest.mark.asyncio
@pytest.mark.parametrize("answer", [None, "", " \n "])
async def test_missing_answer_is_not_a_completed_agent_run(answer):
    provider = ScriptedModelProvider([AssistantTurn(answer)])
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("No tool request expected"))) as client:
        record = await AgentRunner(provider, AgentToolDispatcher(client=client, mode="offline_fixture")).run("question")
    assert record.agent.status == "NO_ANSWER"
    assert record.agent.error.kind == "EMPTY_MODEL_RESPONSE"


@pytest.mark.asyncio
async def test_quota_records_every_id_without_running_extra_tools():
    seen = []
    provider = ScriptedModelProvider([AssistantTurn(tool_calls=[tool("a"), tool("b"), tool("c")])])
    def search(req):
        seen.append(req.url.path)
        return httpx.Response(200, json={"results": []})
    async with httpx.AsyncClient(transport=httpx.MockTransport(search)) as client:
        runner = AgentRunner(provider, AgentToolDispatcher(client=client, mode="offline_fixture"), max_tool_calls=1)
        record = await runner.run("search")
    assert record.agent.status == "TOOL_LIMIT"
    assert [r.call_id for r in record.agent.tool_calls] == ["a", "b", "c"]
    assert [r.error.kind for r in record.agent.tool_calls[1:]] == ["TOOL_LIMIT", "TOOL_LIMIT"]
    assert seen == ["/search"]
    assert len(provider.received_messages) == 1


@pytest.mark.asyncio
async def test_tool_deadline_records_remaining_ids_without_new_execution():
    provider = ScriptedModelProvider([AssistantTurn(tool_calls=[tool("a"), tool("b"), tool("c")])])
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("No transport request"))) as client:
        dispatcher = AgentToolDispatcher(client=client, mode="offline_fixture")
        calls = []
        async def slow(name, args):
            calls.append(name)
            await asyncio.sleep(0.2)
            return {"status": "PASS"}
        dispatcher.execute = slow
        record = await AgentRunner(provider, dispatcher, timeout=0.02).run("slow tools")
    assert record.agent.status == "TIMEOUT"
    assert [r.call_id for r in record.agent.tool_calls] == ["a", "b", "c"]
    assert all(r.error.kind == "TIMEOUT" for r in record.agent.tool_calls)
    assert calls == ["search_web"]


def completion(*, content=None, calls=None, choices=True):
    message = {"role": "assistant", "content": content, "tool_calls": calls or None}
    return {"id": "chatcmpl-offline-qa", "object": "chat.completion", "created": 1,
            "model": "qa-offline-model", "choices": [{"index": 0, "message": message,
            "finish_reason": "tool_calls" if calls else "stop", "logprobs": None}] if choices else [],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}


def wire_tool(identifier, name, args):
    return {"id": identifier, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


@pytest.mark.asyncio
@pytest.mark.parametrize("choice", ["auto", "required", "none"])
async def test_actual_sdk_serializes_model_tools_and_tool_choice(choice):
    seen = []
    def model(req):
        seen.append(req)
        return httpx.Response(200, json=completion(content="7"))
    client = httpx.AsyncClient(transport=httpx.MockTransport(model), trust_env=False)
    provider = OpenAIChatProvider(model="qa-offline-model", base_url="https://model.example.org/v1",
                                  api_key="qa-not-a-real-key", http_client=client)
    try:
        turn = await provider.complete([{"role": "user", "content": "3+4"}], tool_choice=choice)
    finally:
        await provider.aclose()
    assert turn.content == "7" and not turn.tool_calls
    assert len(seen) == 1 and seen[0].url.path == "/v1/chat/completions"
    payload = json.loads(seen[0].content)
    assert payload["model"] == "qa-offline-model"
    assert payload["tools"] == TOOL_SCHEMAS and payload["tool_choice"] == choice


@pytest.mark.asyncio
async def test_actual_sdk_search_read_answer_returns_matching_tool_ids():
    wire, core = [], []
    responses = [completion(calls=[wire_tool("s", "search_web", {"query": "test"})]),
                 completion(calls=[wire_tool("r", "read_webpage", {"url": URL})]),
                 completion(content=f"Evidence: {URL}")]
    def model(req):
        wire.append(json.loads(req.content))
        return httpx.Response(200, json=responses.pop(0))
    def source(req):
        core.append(req.url.path)
        if req.url.path == "/search":
            return httpx.Response(200, json={"results": [{"url": URL, "title": "Article"}]})
        return httpx.Response(200, content=ARTICLE, headers={"Content-Type": "text/html"})
    model_client = httpx.AsyncClient(transport=httpx.MockTransport(model), trust_env=False)
    provider = OpenAIChatProvider(model="qa-offline-model", base_url="https://model.example.org/v1",
                                  api_key="qa-not-a-real-key", http_client=model_client)
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(source), trust_env=False) as client:
            record = await AgentRunner(provider, AgentToolDispatcher(client=client, mode="offline_fixture")).run("search then read")
    finally:
        await provider.aclose()
    assert record.agent.status == "DONE"
    assert core == ["/search", "/article"] and len(wire) == 3
    assert [r.call_id for r in record.agent.tool_calls] == ["s", "r"]
    assert wire[1]["messages"][-1]["tool_call_id"] == "s"
    assert wire[2]["messages"][-1]["tool_call_id"] == "r"
    assert "B00_ARTICLE_CORE" in json.loads(wire[2]["messages"][-1]["content"])["selected_text"]
    assert record.agent.cited_urls == [URL]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 429, 503])
async def test_actual_sdk_error_is_bounded_without_retries_or_secret_trace(status):
    hits = []
    def model(req):
        hits.append(req.url.path)
        return httpx.Response(status, json={"error": {"message": "offline test failure", "type": "qa_error"}})
    client = httpx.AsyncClient(transport=httpx.MockTransport(model), trust_env=False)
    provider = OpenAIChatProvider(model="qa-offline-model", base_url="https://model.example.org/v1",
                                  api_key="qa-not-a-real-key", http_client=client)
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("No tool request"))) as source:
            record = await AgentRunner(provider, AgentToolDispatcher(client=source, mode="offline_fixture")).run("question")
    finally:
        await provider.aclose()
    assert record.agent.status == "MODEL_ERROR"
    assert len(hits) == 1 and not record.agent.tool_calls
    assert "qa-not-a-real-key" not in record.model_dump_json()


@pytest.mark.asyncio
async def test_actual_sdk_no_choices_is_reported_as_model_error():
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=completion(choices=False))))
    provider = OpenAIChatProvider(model="qa-offline-model", base_url="https://model.example.org/v1",
                                  api_key="qa-not-a-real-key", http_client=client)
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("No tool request"))) as source:
            record = await AgentRunner(provider, AgentToolDispatcher(client=source, mode="offline_fixture")).run("question")
    finally:
        await provider.aclose()
    assert record.agent.status == "MODEL_ERROR" and not record.agent.tool_calls
