"""readability-lxml adapter. summary() produces HTML, not plain text."""
from __future__ import annotations

from readability import Document

from local_search_demo.parsers.common import html_fragment_to_text
from local_search_demo.schemas import ParserResult


def parse(html: str, *, url: str | None = None) -> ParserResult:
    document = Document(html, url=url)
    # Read title before summary: summary() mutates its own DOM.
    title = document.title()
    summary_html = document.summary()
    text = html_fragment_to_text(summary_html)
    return ParserResult(
        name="readability",
        status="PASS" if text else "EMPTY",
        raw_output=summary_html or None,
        text=text or None,
        title=title or None,
        chars=len(text),
        metadata={"output_format": "html", "normalized_with": "selectolax"},
    )
