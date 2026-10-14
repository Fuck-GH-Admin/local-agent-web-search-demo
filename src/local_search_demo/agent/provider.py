"""B06 provider abstraction, SDK chat-completions path, and scripted offline model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from local_search_demo.agent.toolspec import TOOL_SCHEMAS


@dataclass(frozen=True)
class RequestedTool:
    call_id: str
    name: str
    arguments_json: str


@dataclass(frozen=True)
class AssistantTurn:
    content: str | None = None
    tool_calls: list[RequestedTool] = field(default_factory=list)


class ModelProvider(Protocol):
    provider_name: str
    model: str
    api_mode: str

    async def complete(self, messages: list[dict[str, Any]], *, tool_choice: str = "auto") -> AssistantTurn:
        ...


class ScriptedModelProvider:
    """Deterministic B06 mock; does not connect to any model or API."""

    provider_name = "scripted-offline"
    model = "fixture-model"
    api_mode = "chat_completions"

    def __init__(self, turns: list[AssistantTurn]):
        self.turns = list(turns)
        self.received_messages: list[list[dict]] = []
        self.tool_choices: list[str] = []

    async def complete(self, messages: list[dict[str, Any]], *, tool_choice: str = "auto") -> AssistantTurn:
        self.received_messages.append([dict(m) for m in messages])
        self.tool_choices.append(tool_choice)
        if not self.turns:
            raise RuntimeError("Scripted model exhausted")
        return self.turns.pop(0)


class OpenAIChatProvider:
    """SDK request adapter only. Actual provider compatibility is tested in B07."""

    provider_name = "openai-compatible"
    api_mode = "chat_completions"

    def __init__(self, *, model: str, base_url: str, api_key: str,
                 timeout: float = 20.0, api_mode: str = "chat_completions",
                 http_client: httpx.AsyncClient | None = None):
        if api_mode != "chat_completions":
            raise ValueError(
                f"UNSUPPORTED_API_MODE: {api_mode!r}; B06 only implements chat_completions"
            )
        if not model.strip() or not base_url.startswith(("http://", "https://")) or not api_key:
            raise ValueError("model, HTTP(S) base_url and API key must be configured")
        from openai import AsyncOpenAI

        self.model = model
        self._client = AsyncOpenAI(
            base_url=base_url, api_key=api_key, timeout=timeout, max_retries=0,
            http_client=http_client,
        )

    async def complete(self, messages: list[dict[str, Any]], *, tool_choice: str = "auto") -> AssistantTurn:
        if tool_choice not in ("auto", "required", "none"):
            raise ValueError("Unsupported tool_choice")
        result = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice=tool_choice,
        )
        if not result.choices:
            raise RuntimeError("Model returned no choices")
        message = result.choices[0].message
        requests = [
            RequestedTool(
                call_id=call.id, name=call.function.name,
                arguments_json=call.function.arguments,
            )
            for call in (message.tool_calls or [])
        ]
        return AssistantTurn(content=message.content, tool_calls=requests)

    async def aclose(self) -> None:
        await self._client.close()
