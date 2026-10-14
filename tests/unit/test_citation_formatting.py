"""Observed Chinese/Markdown citation boundaries must preserve exact provenance."""
import json
from pathlib import Path

import httpx
import pytest

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.agent.provider import AssistantTurn, RequestedTool, ScriptedModelProvider
from local_search_demo.agent.runner import AgentRunner

URL = "https://example.org/article"
ARTICLE = (Path(__file__).resolve().parents[1] / "fixtures/html/static_article.html").read_bytes()


async def scenario(answer):
    model = ScriptedModelProvider([
        AssistantTurn(tool_calls=[RequestedTool("search", "search_web", '{"query":"source"}')]),
        AssistantTurn(tool_calls=[RequestedTool("read", "read_webpage", json.dumps({"url": URL}))]),
        AssistantTurn(content=answer),
    ])
    def source(request):
        if request.url.path == "/search":
            return httpx.Response(200, json={"results": [{"url": URL, "title": "Article"}]})
        return httpx.Response(200, content=ARTICLE, headers={"Content-Type": "text/html"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(source)) as client:
        return await AgentRunner(model, AgentToolDispatcher(client=client, mode="offline_fixture")).run("read source")


@pytest.mark.asyncio
@pytest.mark.parametrize("answer", [
    f"根据官方网页（{URL}）：正文如此。", f"{URL}（已实际读取，HTTP 200）",
    f"网页：`{URL}`", f"来源“{URL}”", f"参见 {URL}。", f"[source]({URL})",
])
async def test_citation_presentation_keeps_successful_source(answer):
    record = await scenario(answer)
    assert record.agent.status == "DONE"
    assert record.agent.cited_urls == [URL]
    assert record.agent.unverified_citations == []


@pytest.mark.asyncio
@pytest.mark.parametrize("url", [
    "https://example.org.attacker.invalid/article", URL + "/other", URL + "?extra=1",
])
async def test_similar_host_path_or_query_is_still_unverified(url):
    record = await scenario(f"来源（{url}）。")
    assert record.agent.status == "UNVERIFIED_CITATION"
    assert record.agent.cited_urls == []
    assert record.agent.unverified_citations == [url]
