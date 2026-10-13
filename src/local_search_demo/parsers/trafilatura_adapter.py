"""Trafilatura adapter: structured article content + metadata in one extraction."""
from __future__ import annotations

import json

import trafilatura

from local_search_demo.parsers.common import normalize_text
from local_search_demo.schemas import ParserResult


def parse(html: str, *, url: str | None = None) -> ParserResult:
    raw = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=True,
    )
    if not raw:
        return ParserResult(name="trafilatura", status="EMPTY")
    payload = json.loads(raw)
    text = normalize_text(payload.get("text"))
    metadata = {
        key: payload[key]
        for key in ("author", "date", "sitename", "hostname", "description", "language", "url")
        if payload.get(key) is not None
    }
    return ParserResult(
        name="trafilatura",
        status="PASS" if text else "EMPTY",
        raw_output=raw, text=text or None,
        title=payload.get("title"),
        chars=len(text),
        metadata={"output_format": "json", **metadata},
    )
