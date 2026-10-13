"""A transparent DOM-based fallback. Not a general article-ranking algorithm."""
from __future__ import annotations

from selectolax.lexbor import LexborHTMLParser

from local_search_demo.parsers.common import normalize_text, BLOCK_TAGS
from local_search_demo.schemas import ParserResult

SELECTORS = (
    "article", "main", '[role="main"]',
    '[itemprop="articleBody"]', ".article-body", ".post-content",
    "#content", ".content",
)


def parse(html: str, *, url: str | None = None) -> ParserResult:
    tree = LexborHTMLParser(html)
    title_node = tree.css_first("title")
    title = normalize_text(title_node.text()) if title_node else None
    for node in tree.css(BLOCK_TAGS + ", nav, footer, aside, header"):
        node.decompose()

    matched_selector = None
    selected = None
    text = ""
    for selector in SELECTORS:
        for candidate in tree.css(selector):
            possible = normalize_text(candidate.text(separator="\n", strip=True, skip_empty=True))
            if possible:
                matched_selector = selector
                selected, text = candidate, possible
                break
        if selected:
            break
    # A visible body can be useful for pages without semantic article containers;
    # however, a JS-only shell remains EMPTY because scripts are removed above.
    if selected is None and tree.body is not None:
        possible = normalize_text(tree.body.text(separator="\n", strip=True, skip_empty=True))
        if possible:
            selected, text, matched_selector = tree.body, possible, "body(fallback)"
    return ParserResult(
        name="selectolax",
        status="PASS" if text else "EMPTY",
        raw_output=selected.html if selected is not None else None,
        text=text or None,
        title=title,
        chars=len(text),
        metadata={"selected_selector": matched_selector, "output_format": "html"},
    )
