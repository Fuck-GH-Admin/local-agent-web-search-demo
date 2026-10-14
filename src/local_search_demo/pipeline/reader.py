"""B04 shared read core: exactly one HTTP fetch, three independent parsers."""
from __future__ import annotations

import time
from pathlib import Path

import httpx

from local_search_demo.fetch.httpx_fetcher import (
    FetchedHTML, HTMLFetcher, create_http_client, save_html,
    DEFAULT_MAX_BYTES, DEFAULT_TIMEOUT,
)
from local_search_demo.parsers.comparison import compare_downloaded
from local_search_demo.pipeline.chooser import choose_result
from local_search_demo.schemas import ExperimentRecord, ReadResult


def read_downloaded(doc: FetchedHTML) -> ReadResult:
    """Accept B02 response bytes, independent from the network and the model."""
    results = compare_downloaded(doc)
    chosen, reason, evidence = choose_result(results)
    return ReadResult(
        fetch=doc.result,
        parsers=results,
        selected_parser=chosen.name if chosen else None,
        selected_text=chosen.text if chosen else None,
        selection_reason=reason if doc.result.status == "PASS"
        else f"Fetch status={doc.result.status}; no parsers executed.",
        selection_evidence=evidence,
    )


async def read_webpage(
    url: str,
    *,
    client: httpx.AsyncClient | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    save_raw: Path | None = None,
) -> ExperimentRecord:
    """One download then all parser outputs, using caller's shared client if set."""
    started = time.perf_counter()
    if client is None:
        async with create_http_client() as owned:
            return await read_webpage(
                url, client=owned, timeout=timeout, max_bytes=max_bytes, save_raw=save_raw
            )
    doc = await HTMLFetcher(client).fetch(url, timeout=timeout, max_bytes=max_bytes)
    if save_raw is not None and doc.result.status == "PASS":
        save_html(doc, save_raw)
    read = read_downloaded(doc)
    return ExperimentRecord(
        mode="read", url=url, fetch=read.fetch, parsers=read.parsers,
        selected_parser=read.selected_parser,
        selected_text=read.selected_text,
        selection_reason=read.selection_reason,
        selection_evidence=read.selection_evidence,
        total_elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
    )
