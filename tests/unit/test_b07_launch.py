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


def test_live_read_gate_is_now_passed_but_missing_credentials_still_blocks(tmp_path):
    env=os.environ.copy()
    for name in ("OPENAI_MODEL","OPENAI_BASE_URL","OPENAI_API_KEY"):
        env.pop(name,None)
    proc=subprocess.run(
        [sys.executable,str(SCRIPT),"--question","test","--allow-live-read",
         "--output",str(tmp_path/"should-not-exist.json")],
        cwd=ROOT,capture_output=True,text=True,timeout=15,env=env,
    )
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["status"]=="BLOCKED"
    assert not (tmp_path/"should-not-exist.json").exists()


def test_current_b06_security_gate_is_satisfied():
    ok, reason = gate_fn()()
    assert ok is True, reason


def test_required_tool_choice_only_for_initial_turn():
    import asyncio
    import httpx
    from local_search_demo.agent.provider import (
        ScriptedModelProvider, AssistantTurn, RequestedTool,
    )
    from local_search_demo.agent.runner import AgentRunner
    from local_search_demo.agent.dispatcher import AgentToolDispatcher

    async def scenario():
        def mock_response(request):
            return httpx.Response(200, json={
                "results": [{"title": "Python docs", "url": "https://docs.python.org/3/"}]
            })
        async with httpx.AsyncClient(transport=httpx.MockTransport(mock_response)) as client:
            model=ScriptedModelProvider([
                AssistantTurn(tool_calls=[
                    RequestedTool("call-1", "search_web", '{"query":"Python docs"}')
                ]),
                AssistantTurn(content="The tool completed."),
            ])
            dispatcher=AgentToolDispatcher(
                client=client, mode="offline_fixture", searxng_base_url="http://mock.searxng",
            )
            record=await AgentRunner(model,dispatcher,tool_choice="required").run("Look up Python docs")
            return record,model

    result,model=asyncio.run(scenario())
    assert result.agent.status=="DONE"
    assert len(result.agent.tool_calls)==1
    assert model.tool_choices==["required","auto"]
