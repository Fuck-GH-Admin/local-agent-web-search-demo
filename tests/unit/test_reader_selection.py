"""B04 heuristic is explainable, stable and does not change parser evidence."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_search_demo.parsers.comparison import compare_parsers
from local_search_demo.pipeline.chooser import choose_result
from local_search_demo.schemas import ParserResult

ROOT = Path(__file__).resolve().parents[1] / "fixtures/html"


def sample(name: str) -> list[ParserResult]:
    return compare_parsers((ROOT / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("filename,expect", [
    ("static_article.html", True),
    ("news_navigation.html", True),
    ("technical_documentation.html", True),
    ("short_chinese.html", True),
    ("malformed.html", True),
    ("spa_empty.html", False),
])
def test_selection_has_complete_audit_and_real_text(filename, expect):
    candidates = sample(filename)
    chosen, reason, audit = choose_result(candidates)
    assert len(audit) == 3
    assert {entry["name"] for entry in audit} == {"trafilatura", "readability", "selectolax"}
    if expect:
        assert chosen and chosen.text
        assert chosen.name in {p.name for p in candidates}
        assert "Alternatives:" in reason
        assert "not a verified" in reason
    else:
        assert chosen is None
        assert "No parser" in reason


def test_noise_affected_technical_docs_not_preferred():
    records = sample("technical_documentation.html")
    chosen, reason, notes = choose_result(records)
    assert chosen is not None
    assert chosen.name != "readability"
    assert "Readability" not in reason or "readability" in reason
    assert len([n for n in notes if n["eligible"]]) == 3


def test_empty_and_failed_are_not_promoted():
    items = [
        ParserResult(name="trafilatura", status="EMPTY", chars=0),
        ParserResult(name="readability", status="FAIL", error=None),
        ParserResult(name="selectolax", status="NOT_RUN"),
    ]
    winner, reason, notes = choose_result(items)
    assert winner is None
    assert all(not n["eligible"] for n in notes)


def test_readability_remains_eligible_if_only_reader():
    value = ParserResult(name="readability", status="PASS", text="Some meaningful content", chars=23)
    chosen, reason, notes = choose_result([
        ParserResult(name="trafilatura", status="FAIL"), value,
        ParserResult(name="selectolax", status="EMPTY", chars=0),
    ])
    assert chosen is value
    assert len(notes) == 3
