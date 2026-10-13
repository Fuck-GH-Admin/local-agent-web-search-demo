"""B03 comparison: run all adapters on the SAME HTML without making web requests.

Each failure is isolated so one broken or missing algorithm does not prevent
others from returning observations. B04 will later choose a winner.
"""
from __future__ import annotations

from collections.abc import Callable
import time

from local_search_demo.parsers import (
    readability_adapter, selectolax_adapter, trafilatura_adapter,
)
from local_search_demo.schemas import ErrorDetail, ParserResult

ADAPTERS: tuple[tuple[str, Callable], ...] = (
    ("trafilatura", trafilatura_adapter.parse),
    ("readability", readability_adapter.parse),
    ("selectolax", selectolax_adapter.parse),
)


def compare_parsers(html: str, *, url: str | None = None) -> list[ParserResult]:
    results: list[ParserResult] = []
    for name, fn in ADAPTERS:
        started = time.perf_counter()
        try:
            result = fn(html, url=url)
            if result.name != name:
                raise ValueError("Adapter name mismatch")
            result.elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        except Exception as exc:
            result = ParserResult(
                name=name, status="FAIL",
                error=ErrorDetail(kind="PARSER_ERROR", message=f"{type(exc).__name__}: {str(exc)[:240]}"),
                elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
            )
        results.append(result)
    return results


def compare_downloaded(document: object) -> list[ParserResult]:
    """Accept B02 FetchedHTML. Never retry failed downloads or fetch again."""
    if getattr(document.result, "status", None) != "PASS" or document.html is None:
        return [ParserResult(name=name, status="NOT_RUN") for name, _ in ADAPTERS]
    return compare_parsers(document.html, url=document.result.url_final)
