"""B07 launch-preflight tests; no real provider or user API credentials needed."""
from __future__ import annotations

from pathlib import Path
from runpy import run_path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/b07-agent-live.py"


def gate_fn():
    return run_path(str(SCRIPT))["live_read_gate"]


def test_g6_gate_fails_closed_when_evidence_missing(tmp_path):
    gate = gate_fn()
    assert gate(index_file=tmp_path/"none.md",report_file=tmp_path/"none.json")[0] is False


def test_g6_gate_rejects_unpassed_index_or_partial_tls_smoke(tmp_path):
    gate=gate_fn()
    idx=tmp_path/"index.md"
    rep=tmp_path/"smoke.json"
    idx.write_text("| **B06-URL-SEC-01** | safety | **NOT_RUN** | details |\n",encoding="utf8")
    rep.write_text(json.dumps({"status":"PASS","rows":[{"status":"PASS"},{"status":"PASS"}]}))
    assert gate(index_file=idx,report_file=rep)[0] is False
    idx.write_text("| **B06-URL-SEC-01** | safety | **PASS (signed)** | details |\n",encoding="utf8")
    rep.write_text(json.dumps({"status":"BLOCKED_OR_FAIL","rows":[{"status":"PASS"},{"status":"FAIL"}]}))
    assert gate(index_file=idx,report_file=rep)[0] is False
    rep.write_text(json.dumps({"status":"PASS","rows":[{"status":"PASS"},{"status":"PASS"}]}))
    assert gate(index_file=idx,report_file=rep)[0] is True


def test_no_model_secrets_means_cli_blocks_without_network(tmp_path):
    env=os.environ.copy()
    for key in ("OPENAI_MODEL","OPENAI_BASE_URL","OPENAI_API_KEY"):
        env.pop(key,None)
    proc=subprocess.run(
        [sys.executable,str(SCRIPT),"--question","What is 2+2?",
         "--output",str(tmp_path/"should-not-exist.json")],
        cwd=ROOT,capture_output=True,text=True,timeout=15,env=env,
    )
    assert proc.returncode == 2
    info=json.loads(proc.stdout)
    assert info["status"]=="BLOCKED"
    assert not (tmp_path/"should-not-exist.json").exists()


def test_unsupported_api_mode_is_rejected_before_network(tmp_path):
    proc=subprocess.run(
        [sys.executable,str(SCRIPT),"--question","test","--api-mode","responses",
         "--output",str(tmp_path/"should-not-exist.json")],
        cwd=ROOT,capture_output=True,text=True,timeout=15,
    )
    assert proc.returncode == 2
    assert "NOT_IMPLEMENTED" in proc.stderr
    assert not (tmp_path/"should-not-exist.json").exists()


def test_live_read_operator_opt_in_uses_current_g6_evidence(tmp_path):
    gate = gate_fn()
    ok, reason = gate()
    assert ok, reason  # Main has the signed-off B06 technical evidence.
    env = os.environ.copy()
    for name in ("OPENAI_MODEL", "OPENAI_BASE_URL", "OPENAI_API_KEY"):
        env.pop(name, None)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--question", "test", "--allow-live-read",
         "--output", str(tmp_path / "should-not-exist.json")],
        cwd=ROOT, capture_output=True, text=True, timeout=15, env=env,
    )
    assert proc.returncode == 2
    assert "Missing OPENAI_MODEL" in proc.stdout
    assert not (tmp_path / "should-not-exist.json").exists()



def test_g4_review_requires_real_auto_search_read_and_verified_citation():
    from runpy import run_path
    script = ROOT / "scripts/b07-g4-review.py"
    module = run_path(str(script))
    evaluate = module["evaluate"]
    render = module["render_markdown"]
    sample = {
        "real_model_invoked": True, "provider": "openai-compatible",
        "tool_choice": "auto", "live_read_enabled": True,
        "agent_trace": {
            "status": "DONE", "answer": "Proof from https://public.example.org/one",
            "cited_urls": ["https://public.example.org/one"],
            "unverified_citations": [],
            "tool_calls": [
                {"call_id": "s1", "name": "search_web", "status": "PASS",
                 "result": {"items": [{"url": "https://public.example.org/one"}]}},
                {"call_id": "r1", "name": "read_webpage", "status": "PASS",
                 "result": {"url": "https://public.example.org/one",
                            "selected_text": "PAGE_CONTENT_PRIVATE_PLACEHOLDER"}},
            ],
        },
    }
    review = evaluate(sample)
    assert review["candidate"] == "READY_FOR_HUMAN_REVIEW"
    assert review["human_signoff"] == "NOT_RUN"
    markdown = render(review)
    assert "PAGE_CONTENT_PRIVATE_PLACEHOLDER" not in markdown
    assert "https://public.example.org/one" not in markdown
    sample["tool_choice"] = "required"
    assert evaluate(sample)["candidate"] == "NOT_READY"
    sample["tool_choice"] = "auto"
    sample["agent_trace"]["cited_urls"] = ["https://unsupported.example.org/"]
    assert evaluate(sample)["candidate"] == "NOT_READY"
    sample["agent_trace"]["cited_urls"] = ["https://public.example.org/one"]
    sample["agent_trace"]["tool_calls"] = list(reversed(sample["agent_trace"]["tool_calls"]))
    assert evaluate(sample)["candidate"] == "NOT_READY"


def test_no_raw_b07_json_traces_are_git_tracked():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "reports/B07/*.json" in ignore
