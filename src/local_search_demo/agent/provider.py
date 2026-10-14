"""B06 provider abstraction, SDK chat-completions path, and scripted offline model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
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
    reasoning_content: str | None = None


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
                 http_client: httpx.AsyncClient | None = None,
                 thinking: str | None = None, max_tokens: int | None = None):
        if api_mode != "chat_completions":
            raise ValueError(
                f"UNSUPPORTED_API_MODE: {api_mode!r}; B06 only implements chat_completions"
            )
        if not model.strip() or not base_url.startswith(("http://", "https://")) or not api_key:
            raise ValueError("model, HTTP(S) base_url and API key must be configured")
        if thinking not in (None, "enabled", "disabled"):
            raise ValueError("thinking must be enabled, disabled or unset")
        if max_tokens is not None and (type(max_tokens) is not int or max_tokens < 1):
            raise ValueError("max_tokens must be a positive integer")
        from openai import AsyncOpenAI

        self.model = model
        self.thinking = thinking
        self.max_tokens = max_tokens
        self.call_log: list[dict[str, Any]] = []
        self._client = AsyncOpenAI(
            base_url=base_url, api_key=api_key, timeout=timeout, max_retries=0,
            http_client=http_client,
        )

    async def complete(self, messages: list[dict[str, Any]], *, tool_choice: str = "auto") -> AssistantTurn:
        if tool_choice not in ("auto", "required", "none"):
            raise ValueError("Unsupported tool_choice")
        options: dict[str, Any] = {}
        if self.thinking is not None:
            options["extra_body"] = {"thinking": {"type": self.thinking}}
        if self.max_tokens is not None:
            options["max_tokens"] = self.max_tokens
        event: dict[str, Any] = {
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "tool_choice": tool_choice, "status": "STARTED",
        }
        self.call_log.append(event)
        started = time.perf_counter()
        try:
            result = await self._client.chat.completions.create(
                model=self.model, messages=messages, tools=TOOL_SCHEMAS,
                tool_choice=tool_choice, **options,
            )
            event.update({
                "status": "RESPONSE", "response_id": result.id,
                "response_model": result.model,
                "finish_reason": result.choices[0].finish_reason if result.choices else None,
                "usage": result.usage.model_dump(mode="json") if result.usage else None,
            })
        except BaseException as exc:
            # Never copy exception messages, headers or request bodies: they
            # may contain credentials or private provider response content.
            event.update({"status": "ERROR", "error_type": type(exc).__name__,
                          "http_status": getattr(exc, "status_code", None)})
            raise
        finally:
            event["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        if not result.choices:
            raise RuntimeError("Model returned no choices")
        if result.choices[0].finish_reason not in ("stop", "tool_calls"):
            raise RuntimeError("Model response did not finish normally")
        message = result.choices[0].message
        requests = [
            RequestedTool(
                call_id=call.id, name=call.function.name,
                arguments_json=call.function.arguments,
            )
            for call in (message.tool_calls or [])
        ]
        return AssistantTurn(content=message.content, tool_calls=requests,
                             reasoning_content=getattr(message, "reasoning_content", None))

    async def aclose(self) -> None:
        await self._client.close()
