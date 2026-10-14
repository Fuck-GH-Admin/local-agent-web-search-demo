"""Interface safety and timing contracts, without any paid API requests."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from local_search_demo.agent.provider import AssistantTurn, OpenAIChatProvider
from local_search_demo.agent.service import AgentConfigurationError, execute_agent
from local_search_demo.web.api import create_app


class NeverCalled:
    provider_name = "offline-guard"
    model = "guard"
    api_mode = "chat_completions"

    async def complete(self, *args, **kwargs):
        pytest.fail("Invalid configuration must not reach the model")


@pytest.mark.asyncio
@pytest.mark.parametrize("options", [
    {"timeout": float("nan")}, {"max_rounds": 1.5}, {"max_rounds": True},
    {"thinking": "typo"}, {"allow_live_read": "false"},
])
async def test_invalid_service_options_never_invoke_model(options):
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("No HTTP expected"))) as client:
        with pytest.raises(AgentConfigurationError):
            await execute_agent("test", search_client=client, provider=NeverCalled(), **options)


def test_api_validation_does_not_echo_submitted_secret_or_create_provider():
    created = []
    app = create_app(agent_provider_factory=lambda: created.append(True) or NeverCalled())
    with TestClient(app) as client:
        response = client.post("/api/agent", json={"question": "test", "api_key": "PRIVATE_SENTINEL"})
    assert response.status_code == 422
    assert "PRIVATE_SENTINEL" not in response.text
    assert created == []


def test_whitespace_question_is_rejected_before_provider_construction():
    created = []
    app = create_app(agent_provider_factory=lambda: created.append(True) or NeverCalled())
    with TestClient(app) as client:
        response = client.post("/api/agent", json={"question": " \n "})
    assert response.status_code == 422
    assert created == []


@pytest.mark.asyncio
async def test_shared_service_preserves_actual_sdk_model_and_core_measurements(monkeypatch):
    import local_search_demo.agent.service as service
    def reply(request):
        return httpx.Response(200, json={
            "id": "offline-timing", "model": "fixture", "object": "chat.completion", "created": 1,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "7"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
        })
    def factory(**options):
        return OpenAIChatProvider(**options, http_client=httpx.AsyncClient(transport=httpx.MockTransport(reply)))
    monkeypatch.setenv("OPENAI_MODEL", "fixture")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://fixture.example")
    monkeypatch.setenv("OPENAI_API_KEY", "PRIVATE_SENTINEL")
    monkeypatch.setattr(service, "OpenAIChatProvider", factory)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("No tool expected"))) as search:
        record = await execute_agent("3+4", search_client=search)
    assert record.agent.status == "DONE"
    assert record.agent.model_calls[0]["usage"]["total_tokens"] == 11
    assert record.agent.model_calls[0]["elapsed_ms"] >= 0
    assert record.agent.core_execution_evidence == []
    assert "PRIVATE_SENTINEL" not in record.model_dump_json()
