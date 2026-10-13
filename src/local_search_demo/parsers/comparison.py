"""B03 comparison: run all adapters on the SAME HTML without making web requests.

Each failure is isolated so one broken or missing algorithm does not prevent
others from returning observations. B04 will later choose a winner.
"""
from __future__ import annotations

from collections.abc import Callable
import importlib
import time

from local_search_demo.schemas import ErrorDetail, ParserResult


def _adapter(name: str) -> Callable:
    def parse(html: str, *, url: str | None = None) -> ParserResult:
        # Import inside the per-parser try block: unavailable adapters must
        # produce an isolated failure rather than prevent comparison startup.
        module = importlib.import_module(f"local_search_demo.parsers.{name}_adapter")
        return module.parse(html, url=url)
    return parse


ADAPTERS: tuple[tuple[str, Callable], ...] = (
    ("trafilatura", _adapter("trafilatura")),
    ("readability", _adapter("readability")),
    ("selectolax", _adapter("selectolax")),
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
