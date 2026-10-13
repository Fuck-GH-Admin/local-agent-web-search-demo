import json
from html.parser import HTMLParser
from pathlib import Path

FIXTURES = Path(__file__).parents[1] / "fixtures"

class FixtureParser(HTMLParser):
    pass


def test_six_offline_html_fixtures_exist_and_parse():
    expected = {
        "article.html", "noisy_news.html", "tech_docs.html", "short_zh.html",
        "spa_shell.html", "malformed.html",
    }
    actual = {p.name for p in (FIXTURES / "html").glob("*.html")}
    assert expected <= actual
    for name in expected:
        html = (FIXTURES / "html" / name).read_text(encoding="utf-8")
        assert len(html) > 25
        parser = FixtureParser()
        parser.feed(html)


def test_mock_searxng_fixture_shape():
    response = json.loads((FIXTURES / "search" / "results.json").read_text(encoding="utf-8"))
    assert response["query"] == "test query"
    assert response["results"][0]["url"].startswith("https://")
