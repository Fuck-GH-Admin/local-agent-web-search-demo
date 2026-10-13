"""Shared normalization helpers; none of these functions performs network I/O."""
from __future__ import annotations

import re

from selectolax.lexbor import LexborHTMLParser

BLOCK_TAGS = "script, style, template, noscript, iframe, svg, canvas"


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    lines = [re.sub(r"[\t ]+", " ", line).strip() for line in value.splitlines()]
    # Preserve paragraph/code boundaries but avoid huge blank gaps.
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def html_fragment_to_text(html: str) -> str:
    tree = LexborHTMLParser(html)
    for tag in tree.css(BLOCK_TAGS):
        tag.decompose()
    node = tree.body or tree.root
    return normalize_text(node.text(separator="\n", strip=True, skip_empty=True)) if node else ""
