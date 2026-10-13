"""B03: parser adapters preserve independently visible extraction outcomes."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_search_demo.parsers import (
    readability_adapter, selectolax_adapter, trafilatura_adapter,
)
from local_search_demo.parsers.comparison import compare_parsers, compare_downloaded
from local_search_demo.schemas import FetchResult

ROOT = Path(__file__).parents[1] / "fixtures"
MANIFEST = json.loads((ROOT / "manifest.json").read_text())
HTML_CASES = [row for row in MANIFEST if row["format"] == "html"]


@pytest.mark.parametrize("sample", HTML_CASES, ids=lambda row: row["id"])
def test_every_fixture_exercises_all_parsers(sample):
    html = (ROOT / sample["path"]).read_text(encoding="utf-8")
    results = compare_parsers(html, url=f"https://example.org/fixtures/{sample['id']}")
    assert [r.name for r in results] == ["trafilatura", "readability", "selectolax"]
    assert all(r.status in {"PASS", "EMPTY"} for r in results)
    assert all(r.elapsed_ms is not None and r.elapsed_ms >= 0 for r in results)
    assert all(r.chars == len(r.text or "") for r in results)
    assert all(r.status != "PASS" or bool(r.text) for r in results)
    # Static article may be filtered by some algorithms; synthetic probes
    # measure this difference instead of silently declaring a winner.
    if sample["expect_body"]:
        assert any(
            all(anchor in (result.text or "") for anchor in sample["expected_body_anchors"][:1])
            for result in results
        )
    for result in results:
        for noise in sample.get("noise_anchors", []):
            if sample["category"] == "spa_empty":
                assert noise not in (result.text or "")


def test_selectolax_article_focus_eliminates_nav_and_ads():
    html = (ROOT / "html/news_navigation.html").read_text()
    result = selectolax_adapter.parse(html)
    assert result.status == "PASS"
    assert result.metadata["selected_selector"] == "article"
    assert "B00_NEWS_CORE" in result.text
    assert "B00_NAV_NOISE" not in result.text
    assert "B00_AD_NOISE" not in result.text
    assert "B00_FOOTER_NOISE" not in result.text
    assert result.raw_output and "<article" in result.raw_output


def test_readability_keeps_raw_html_separate_from_clean_text():
    html = (ROOT / "html/static_article.html").read_text()
    result = readability_adapter.parse(html)
    assert result.status in {"PASS", "EMPTY"}
    assert result.metadata["output_format"] == "html"
    if result.text:
        assert "<p>" not in result.text
        assert result.raw_output and "<" in result.raw_output


def test_trafilatura_raw_result_is_json_and_carries_metadata():
    html = (ROOT / "html/static_article.html").read_text()
    result = trafilatura_adapter.parse(html, url="https://example.org/article")
    assert result.status in {"PASS", "EMPTY"}
    if result.raw_output:
        payload = json.loads(result.raw_output)
        assert "text" in payload
        assert result.metadata["output_format"] == "json"


def test_chinese_selectolax_and_malformed_markup():
    for fixture, anchor in [
        ("short_chinese.html", "短中文正文锚点"),
        ("malformed.html", "B00_MALFORMED_CORE"),
    ]:
        result = selectolax_adapter.parse((ROOT / "html" / fixture).read_text())
        assert result.status == "PASS"
        assert anchor in result.text


def test_readability_does_not_run_scripts_in_spa():
    html = (ROOT / "html/spa_empty.html").read_text()
    for parser in (trafilatura_adapter.parse, readability_adapter.parse, selectolax_adapter.parse):
        result = parser(html)
        assert "B00_SCRIPT_ONLY_NOT_BODY" not in (result.text or "")


def test_each_adapter_error_isolated(monkeypatch):
    import local_search_demo.parsers.comparison as comparison

    def broken(html, *, url=None):
        raise RuntimeError("one parser intentionally fails")

    monkeypatch.setattr(comparison, "ADAPTERS", (
        ("trafilatura", broken),
        ("readability", lambda html, *, url=None: readability_adapter.parse(html, url=url)),
        ("selectolax", lambda html, *, url=None: selectolax_adapter.parse(html, url=url)),
    ))
    result = comparison.compare_parsers("<article><p>Working fallback.</p></article>")
    assert result[0].status == "FAIL"
    assert result[0].error.kind == "PARSER_ERROR"
    assert result[2].status == "PASS"
    assert "Working fallback" in result[2].text


def test_download_adapter_refuses_failed_fetch_without_network():
    from local_search_demo.fetch.httpx_fetcher import FetchedHTML

    result = compare_downloaded(FetchedHTML(
        result=FetchResult(status="FAIL", url_requested="https://example.org"),
        html=None,
    ))
    assert len(result) == 3
    assert all(r.status == "NOT_RUN" for r in result)
