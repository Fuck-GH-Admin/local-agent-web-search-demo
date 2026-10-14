"""Actual SDK wire checks for the DeepSeek options, with no real API calls."""
import json

import httpx
import pytest

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.agent.provider import OpenAIChatProvider
from local_search_demo.agent.runner import AgentRunner


def reply(content="7", calls=None, reasoning=None, finish="stop"):
    return {
        "id": "offline-response", "object": "chat.completion", "created": 1,
        "model": "offline-model", "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
        "choices": [{"index": 0, "finish_reason": finish, "message": {
            "role": "assistant", "content": content, "tool_calls": calls,
            "reasoning_content": reasoning,
        }}],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("thinking", [None, "enabled", "disabled"])
async def test_sdk_thinking_options_token_bound_and_metadata(thinking):
    sent = []
    def respond(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=reply())
    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    provider = OpenAIChatProvider(model="offline-model", base_url="https://api.example.org",
                                  api_key="private-placeholder", http_client=client,
                                  thinking=thinking, max_tokens=256)
    try:
        await provider.complete([{"role": "user", "content": "PRIVATE_QUESTION"}])
    finally:
        await provider.aclose()
    assert sent[0]["max_tokens"] == 256
    if thinking is None:
        assert "thinking" not in sent[0]
    else:
        assert sent[0]["thinking"] == {"type": thinking}
    event = provider.call_log[0]
    assert event["status"] == "RESPONSE" and event["usage"]["total_tokens"] == 12
    assert event["elapsed_ms"] >= 0 and event["response_id"] == "offline-response"
    assert "private-placeholder" not in json.dumps(event)
    assert "PRIVATE_QUESTION" not in json.dumps(event)


@pytest.mark.asyncio
async def test_reasoning_and_matching_tool_results_survive_sdk_followup():
    sent = []
    call = {"id": "sdk-search", "type": "function", "function": {
        "name": "search_web", "arguments": '{"query":"Python docs"}',
    }}
    responses = [reply(None, [call], "PRIVATE_REASONING", "tool_calls"), reply("No results available")]
    def model(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=responses.pop(0))
    provider = OpenAIChatProvider(model="offline-model", base_url="https://api.example.org",
                                  api_key="placeholder", thinking="enabled",
                                  http_client=httpx.AsyncClient(transport=httpx.MockTransport(model)))
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"results": []})
        )) as search:
            record = await AgentRunner(provider, AgentToolDispatcher(client=search, mode="offline_fixture")).run("search")
    finally:
        await provider.aclose()
    assert record.agent.status == "DONE"
    assert sent[1]["messages"][-2]["reasoning_content"] == "PRIVATE_REASONING"
    assert sent[1]["messages"][-1]["tool_call_id"] == "sdk-search"
    assert "PRIVATE_REASONING" not in record.model_dump_json()
    assert "PRIVATE_REASONING" not in json.dumps(provider.call_log)


@pytest.mark.asyncio
async def test_required_becomes_auto_after_first_sdk_tool_result():
    choices = []
    call = {"id": "forced-search", "type": "function", "function": {
        "name": "search_web", "arguments": '{"query":"Python docs"}',
    }}
    def model(request):
        choice = json.loads(request.content)["tool_choice"]
        choices.append(choice)
        return httpx.Response(200, json=reply(None, [call], finish="tool_calls")
                              if choice == "required" else reply("Search completed"))
    provider = OpenAIChatProvider(model="offline-model", base_url="https://api.example.org",
                                  api_key="placeholder", thinking="disabled",
                                  http_client=httpx.AsyncClient(transport=httpx.MockTransport(model)))
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"results": []})
        )) as search:
            record = await AgentRunner(provider, AgentToolDispatcher(client=search, mode="offline_fixture"),
                                       tool_choice="required").run("search")
    finally:
        await provider.aclose()
    assert record.agent.status == "DONE" and choices == ["required", "auto"]


@pytest.mark.asyncio
@pytest.mark.parametrize("finish", ["length", "content_filter", "insufficient_system_resource"])
async def test_incomplete_response_is_not_a_successful_answer(finish):
    provider = OpenAIChatProvider(model="offline-model", base_url="https://api.example.org", api_key="placeholder",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=reply(finish=finish)))))
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("No tool expected"))) as search:
            record = await AgentRunner(provider, AgentToolDispatcher(client=search, mode="offline_fixture")).run("answer")
    finally:
        await provider.aclose()
    assert record.agent.status == "MODEL_ERROR" and record.agent.answer is None
    assert provider.call_log[0]["finish_reason"] == finish


@pytest.mark.asyncio
async def test_provider_error_metadata_does_not_copy_sensitive_error_message():
    provider = OpenAIChatProvider(model="offline-model", base_url="https://api.example.org", api_key="private-placeholder",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(401, json={
            "error": {"message": "private-placeholder PRIVATE_BODY", "type": "test"},
        }))))
    try:
        with pytest.raises(Exception):
            await provider.complete([{"role": "user", "content": "test"}])
    finally:
        await provider.aclose()
    assert provider.call_log[0]["http_status"] == 401 and len(provider.call_log) == 1
    assert "private-placeholder" not in json.dumps(provider.call_log)
    assert "PRIVATE_BODY" not in json.dumps(provider.call_log)
