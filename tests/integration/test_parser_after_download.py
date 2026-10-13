"""B02 -> B03 integration uses one local HTTP request and shared HTML."""
from __future__ import annotations

import httpx
import pytest

from local_search_demo.fetch.httpx_fetcher import HTMLFetcher
from local_search_demo.parsers.comparison import compare_downloaded


@pytest.mark.asyncio
async def test_download_only_once_then_run_three_adapters():
    count = 0
    html = (
        "<html><head><title>One request</title></head><body>"
        "<article><h1>One request</h1><p>B03_INTEGRATION_ANCHOR: "
        "This is shared between all parser adapters.</p></article></body></html>"
    )

    def handler(request):
        nonlocal count
        count += 1
        return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloaded = await HTMLFetcher(client).fetch("https://example.org/b03")
        assert downloaded.result.status == "PASS"
        results = compare_downloaded(downloaded)
    assert count == 1
    assert [x.name for x in results] == ["trafilatura", "readability", "selectolax"]
    assert any("B03_INTEGRATION_ANCHOR" in (x.text or "") for x in results)
