#!/usr/bin/env python3
"""B06 reproducible tool-loop evidence; scripted model, real Core on MockTransport."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path

import httpx

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.agent.provider import AssistantTurn, RequestedTool, ScriptedModelProvider
from local_search_demo.agent.runner import AgentRunner

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "tests/fixtures/html/static_article.html").read_bytes()
SEARCH = json.loads((ROOT / "tests/fixtures/search/success.json").read_text(encoding="utf-8"))


def tool(call_id: str, name: str, payload: dict | str) -> RequestedTool:
    return RequestedTool(call_id, name, payload if isinstance(payload, str) else json.dumps(payload))


async def run() -> dict:
    hits: list[str] = []

    def response(request):
        hits.append(request.url.path)
        if request.url.path == "/search":
            return httpx.Response(200, json=SEARCH)
        if request.url.path == "/article":
            return httpx.Response(200, content=HTML, headers={"Content-Type": "text/html; charset=utf-8"})
        return httpx.Response(404)

    scenarios = [
        ("no_tool", [AssistantTurn("3+4=7")], "DONE", 0),
        ("single_search", [
            AssistantTurn(tool_calls=[tool("s1", "search_web", {"query": "example"})]),
            AssistantTurn("Two results found"),
        ], "DONE", 1),
        ("search_read", [
            AssistantTurn(tool_calls=[tool("s2", "search_web", {"query": "example"})]),
            AssistantTurn(tool_calls=[tool("r2", "read_webpage", {"url": "https://example.org/article"})]),
            AssistantTurn("Evidence: https://example.org/article"),
        ], "DONE", 2),
        ("multi_and_bad_json", [
            AssistantTurn(tool_calls=[
                tool("broken", "search_web", "{bad"),
                tool("s3", "search_web", {"query": "test"}),
                tool("r3", "read_webpage", {"url": "https://example.org/article"}),
            ]),
            AssistantTurn("Completed with logged error"),
        ], "DONE", 3),
    ]
    results = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as client:
        for name, turns, expected_status, calls in scenarios:
            provider = ScriptedModelProvider(turns)
            dispatcher = AgentToolDispatcher(
                client=client, searxng_base_url="http://searxng.mock", mode="offline_fixture",
            )
            record = await AgentRunner(provider, dispatcher, tool_choice="auto").run(name)
            ok = record.agent.status == expected_status and len(record.agent.tool_calls) == calls
            if name == "search_read":
                ok &= (len(record.agent.cited_urls) == 1 and
                       record.agent.tool_calls[-1].status == "PASS" and
                       "B00_ARTICLE_CORE" in record.agent.tool_calls[-1].result.get("selected_text", ""))
            if name == "multi_and_bad_json":
                ok &= record.agent.tool_calls[0].error.kind == "INVALID_JSON"
                ok &= record.agent.tool_calls[-1].status == "PASS"
            results.append({
                "scenario": name, "pass": bool(ok),
                "agent": record.agent.model_dump(mode="json"),
            })
    return {
        "batch": "B06", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "scripted_model_mock_transport_true_Core",
        "status": "PASS" if all(x["pass"] for x in results) else "FAIL",
        "scenarios": results, "mock_transport_paths": hits,
        "real_model_invoked": False, "internet_invoked": False,
        "live_model_controlled_URL_read": "GUARDED_PUBLIC_ONLY; not exercised by this offline script",
    }


def main() -> int:
    output = ROOT / "reports/B06/tool-loop-tests.json"
    result = asyncio.run(run())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "scenarios": len(result["scenarios"]),
        "file": str(output),
    }, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
