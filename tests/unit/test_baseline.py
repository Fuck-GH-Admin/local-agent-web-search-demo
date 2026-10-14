"""Check installation, fixed-input integrity, and shared data serialization offline."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from pydantic import ValidationError
import pytest

from local_search_demo.environment import IMPORTS, environment_report
from local_search_demo.schemas import (
    AgentTrace, ErrorDetail, ExperimentRecord, FetchResult, ParserResult,
    ReadResult, SearchItem, SearchResult, ToolCall,
)
from conftest import MANIFEST


@pytest.mark.parametrize("sample", MANIFEST, ids=lambda sample: sample["id"])
def test_fixture_integrity(sample, fixture_root):
    raw = (fixture_root / sample["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == sample["sha256"]
    text = raw.decode("utf-8")
    if sample["format"] == "json":
        assert isinstance(json.loads(text), dict)
    for anchor in sample["expected_body_anchors"]:
        assert anchor in text


def test_six_html_categories_and_negative_shell(fixture_root):
    html = [s for s in MANIFEST if s["format"] == "html"]
    assert {s["category"] for s in html} == {
        "article", "news_navigation", "technical_docs", "short_chinese", "spa_empty", "malformed"
    }
    shell = next(s for s in html if s["category"] == "spa_empty")
    assert shell["expected_body_anchors"] == []
    assert shell["expect_body"] is False


def test_nested_experiment_json_roundtrip_preserves_unicode_and_failures():
    record = ExperimentRecord(
        mode="agent", query="中文查询",
        search=SearchResult(status="PASS", items=[SearchItem(url="https://example.org/", title="中文标题")]),
        fetch=FetchResult(status="FAIL", url_requested="https://example.org/", http_status=429,
                          error=ErrorDetail(kind="HTTP_429", message="限流")),
        parsers=[ParserResult(name="trafilatura", status="NOT_RUN")],
        agent=AgentTrace(api_mode="responses", tool_calls=[ToolCall(call_id="call-1", name="search_web",
                                                                  arguments={"query": "中文查询"})]),
    )
    restored = ExperimentRecord.model_validate_json(record.model_dump_json())
    assert restored == record
    assert restored.timestamp.utcoffset().total_seconds() == 0
    assert restored.fetch.error.kind == "HTTP_429"
    assert restored.selected_parser is None
    assert restored.agent.answer is None


def test_unexecuted_stages_stay_null_and_lists_are_independent():
    first, second = ExperimentRecord(mode="read"), ExperimentRecord(mode="read")
    payload = first.model_dump(mode="json")
    for key in ("query", "url", "search", "fetch", "selected_parser", "selection_reason", "agent", "total_elapsed_ms"):
        assert payload[key] is None
    first.parsers.append(ParserResult(name="selectolax"))
    assert second.parsers == []
    assert first.run_id != second.run_id
    assert ReadResult().fetch is None


@pytest.mark.parametrize("model,kwargs", [
    (SearchResult, {"elapsed_ms": -1}),
    (FetchResult, {"bytes": -1}),
    (FetchResult, {"http_status": 999}),
    (ParserResult, {"name": "selectolax", "chars": -1}),
    (ParserResult, {"name": "imaginary"}),
    (AgentTrace, {"api_mode": "imaginary"}),
    (ExperimentRecord, {"mode": "agent", "total_elapsed_ms": -1}),
    (ExperimentRecord, {"mode": "search", "unexpected_key": "oops"}),
])
def test_contract_rejects_invalid_metrics_and_unknown_fields(model, kwargs):
    with pytest.raises(ValidationError):
        model(**kwargs)


def test_environment_imports_and_does_not_capture_credentials(monkeypatch):
    sentinel = "B00-PRIVATE-SENTINEL-NEVER-EXPORT"
    for key in ("GITHUB_TOKEN", "OPENAI_API_KEY", "HTTP_PROXY"):
        monkeypatch.setenv(key, sentinel)
    report = environment_report()
    assert report["status"] == "PASS"
    assert {c["package"] for c in report["imports"]} == set(IMPORTS)
    assert sentinel not in json.dumps(report)
    assert report["network_tests"] == "NOT_RUN"
    assert report["model_calls"] == "NOT_RUN"


@pytest.mark.parametrize("command", [[], ["search"], ["read"], ["agent"], ["environment"]])
def test_installed_module_help(command, tmp_path):
    result = subprocess.run([sys.executable, "-m", "local_search_demo", *command, "--help"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage:" in result.stdout


def test_agent_cli_without_credentials_is_blocked_before_any_network(tmp_path):
    env = dict(os.environ, SEARXNG_BASE_URL="http://127.0.0.1:1")
    for secret in ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"):
        env.pop(secret, None)
    result = subprocess.run(
        [sys.executable, "-m", "local_search_demo", "agent", "fixture", "--json"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=8,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "BLOCKED"
    assert "MODEL_NOT_CONFIGURED" in result.stdout


def test_console_entrypoint_help_from_another_directory(tmp_path):
    executable = Path(sys.executable).parent / "local-search-demo"
    result = subprocess.run([str(executable), "--help"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert "environment" in result.stdout


def test_search_now_has_real_input_validation_without_network(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "local_search_demo", "search", "   ", "--json"],
        cwd=tmp_path, capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["mode"] == "search"
    assert payload["search"]["status"] == "FAIL"
    assert payload["search"]["errors"][0]["kind"] == "INVALID_QUERY"


def test_read_is_real_and_invalid_urls_return_structured_error_without_network(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "local_search_demo", "read", "fixture", "--json"],
        cwd=tmp_path, capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 1
    record = json.loads(result.stdout)
    assert record["mode"] == "read"
    assert record["fetch"]["error"]["kind"] == "INVALID_URL"
    assert record["selected_parser"] is None
