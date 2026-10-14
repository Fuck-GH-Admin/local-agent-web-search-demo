"""Shared B07 Agent execution service for CLI and local FastAPI.

The only production integration with models is the tested OpenAIChatProvider.
No API key or provider headers are added to ExperimentRecord. The caller chooses
whether live reads are opt-in; unsafe targets still go through B06 safety.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Callable

import httpx

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.agent.provider import ModelProvider, OpenAIChatProvider
from local_search_demo.agent.runner import AgentRunner
from local_search_demo.schemas import ExperimentRecord

ROOT = Path(__file__).resolve().parents[3]


class AgentConfigurationError(ValueError):
    """Safe, credential-free configuration error."""


def live_read_gate(
    *,
    index_file: Path = ROOT / "docs/OPEN_VALIDATION_INDEX.md",
    report_file: Path = ROOT / "reports/B06/safe-http-live.json",
) -> tuple[bool, str]:
    """Explicit operator signoff check; B06 safe transport enforces actual I/O."""
    try:
        row = next(
            line for line in index_file.read_text(encoding="utf-8").splitlines()
            if line.startswith("| **B06-URL-SEC-01**")
        )
        report = json.loads(report_file.read_text(encoding="utf-8"))
        cells = [c.strip() for c in row.split("|")]
    except (OSError, ValueError, StopIteration):
        return False, "Missing G6 validation evidence"
    if len(cells) < 4 or not cells[3].startswith("**PASS"):
        return False, "B06 URL safety is not signed off"
    if report.get("status") != "PASS":
        return False, "B06 live HTTPS validation is not PASS"
    rows = report.get("rows")
    if not isinstance(rows, list) or len(rows) < 2 or any(
        not isinstance(item, dict) or item.get("status") != "PASS" for item in rows
    ):
        return False, "B06 HTTPS results incomplete"
    return True, "Signed B06 safety evidence present"


def configuration_from_environment(
    *, model: str | None = None, base_url: str | None = None
) -> tuple[str, str, str]:
    model = model or os.getenv("OPENAI_MODEL", "")
    base_url = base_url or os.getenv("OPENAI_BASE_URL", "")
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not model or not base_url or not api_key:
        raise AgentConfigurationError(
            "MODEL_NOT_CONFIGURED: set OPENAI_MODEL, OPENAI_BASE_URL and OPENAI_API_KEY locally"
        )
    if not base_url.startswith(("https://", "http://")):
        raise AgentConfigurationError("MODEL_BASE_URL_INVALID")
    return model, base_url, api_key


async def execute_agent(
    question: str, *,
    search_client: httpx.AsyncClient,
    searxng_base_url: str = "http://127.0.0.1:8080",
    provider: ModelProvider | None = None,
    model: str | None = None,
    base_url: str | None = None,
    thinking: str | None = None,
    max_tokens: int = 1024,
    tool_choice: str = "auto",
    allow_live_read: bool = False,
    timeout: float = 70,
    max_rounds: int = 6,
) -> ExperimentRecord:
    """Run the existing AgentRunner with one call-scoped tool dispatcher.

    A trusted injected provider permits offline MockTransport fixture tests;
    production always uses a separate DNS-pinned transport for live reads.
    """
    if not isinstance(question, str) or not question.strip() or len(question) > 4000:
        raise AgentConfigurationError("Question must be between 1 and 4000 characters")
    if tool_choice not in ("auto", "required", "none"):
        raise AgentConfigurationError("Invalid tool choice")
    if (type(timeout) not in (int, float) or not math.isfinite(timeout)
            or not 0 < timeout <= 120 or type(max_rounds) is not int or not 1 <= max_rounds <= 10):
        raise AgentConfigurationError("Invalid Agent time/round budget")
    if type(max_tokens) is not int or not 1 <= max_tokens <= 4096:
        raise AgentConfigurationError("Invalid max_tokens budget")
    if thinking not in (None, "enabled", "disabled") or type(allow_live_read) is not bool:
        raise AgentConfigurationError("Invalid thinking or live-read option")
    if allow_live_read:
        allowed, reason = live_read_gate()
        if not allowed:
            raise AgentConfigurationError("LIVE_READ_DENIED: " + reason)

    owned = provider is None
    if owned:
        selected_model, selected_base_url, api_key = configuration_from_environment(
            model=model, base_url=base_url,
        )
        if tool_choice == "required" and thinking == "enabled":
            raise AgentConfigurationError("Required tools with thinking=enabled are unsupported")
        provider = OpenAIChatProvider(
            model=selected_model, base_url=selected_base_url, api_key=api_key,
            thinking=thinking, max_tokens=max_tokens, timeout=timeout,
        )
    try:
        fixture = not owned
        dispatcher = AgentToolDispatcher(
            client=search_client,
            searxng_base_url=searxng_base_url,
            mode="offline_fixture" if fixture else "live",
            enable_live_reads=bool(allow_live_read and not fixture),
        )
        record = await AgentRunner(
            provider, dispatcher, tool_choice=tool_choice,
            max_rounds=max_rounds, timeout=timeout,
        ).run(question)
        if record.agent:
            record.agent.model_calls = list(getattr(provider, "call_log", []))
            record.agent.core_execution_evidence = list(dispatcher.execution_evidence)
        return record
    finally:
        if owned:
            await provider.aclose()
