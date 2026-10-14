"""Final acceptance must preserve fresh bytes and reject unbound gate claims."""
import hashlib
import json
from pathlib import Path
import runpy
import sys

import httpx
import pytest

from local_search_demo.pipeline.reader import read_webpage

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/b08-validation.py"
ARTICLE = (ROOT / "tests/fixtures/html/static_article.html").read_bytes()


def test_unbound_approved_signature_is_not_verified(tmp_path, monkeypatch):
    fn = runpy.run_path(str(SCRIPT))["validate_prior_evidence"]
    monkeypatch.setitem(fn.__globals__, "ROOT", tmp_path)
    p = tmp_path / "reports/B07/validation/g4-signoff.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"status": "APPROVED", "gate_result": "PASS"}))
    assert fn()["G4"]["verified"] is False


def test_missing_prior_gate_cannot_yield_successful_precheck(tmp_path, monkeypatch):
    fn = runpy.run_path(str(SCRIPT))["main"]
    monkeypatch.setitem(fn.__globals__, "ROOT", tmp_path)
    monkeypatch.setitem(fn.__globals__, "run_cmd", lambda *a, **k: {"status": "PASS"})
    out = tmp_path / "observations.json"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output", str(out)])
    assert fn() == 2
    assert json.loads(out.read_text())["status"] == "PRECHECK_PARTIAL_G5_NOT_RUN"


@pytest.mark.asyncio
async def test_fresh_capture_keeps_one_original_html_and_never_overwrites_prior(tmp_path, monkeypatch):
    fn = runpy.run_path(str(SCRIPT))["capture_live_pages"]
    monkeypatch.setitem(fn.__globals__, "ROOT", tmp_path)
    monkeypatch.setitem(fn.__globals__, "source_urls", lambda: [("article", "https://example.org/article")])
    hits = []
    def respond(request):
        hits.append(request.url.path)
        return httpx.Response(200, content=ARTICLE.replace(b"B00_ARTICLE_CORE", f"CAPTURE_{len(hits)}".encode()), headers={"Content-Type": "text/html"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        async def capture(url, **kwargs):
            return await read_webpage(url, client=client, **kwargs)
        monkeypatch.setitem(fn.__globals__, "read_webpage", capture)
        first = (await fn(raw=True))[0]
        original = tmp_path / first["private_html"]
        data = original.read_bytes()
        assert first["html_sha256"] == hashlib.sha256(data).hexdigest()
        assert len(first["parsers"]) == 3 and hits == ["/article"]
        assert original.stat().st_mode & 0o777 == 0o600
        second = (await fn(raw=True))[0]
    assert first["private_record"] != second["private_record"]
    assert original.read_bytes() == data
    assert first["html_sha256"] != second["html_sha256"]
    assert hits == ["/article", "/article"]
