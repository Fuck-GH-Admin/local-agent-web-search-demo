#!/usr/bin/env python3
"""Real CLI / FastAPI Agent SDK loopback smoke, with zero paid model requests.

The HTTP server provides an OpenAI-compatible *fixture*, not a real model.
It proves the ordinary CLI and API use the same B07 AgentRunner/Dispatcher
via real HTTP and OpenAI SDK serialization, including tool-call correlation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Thread

from fastapi.testclient import TestClient

from local_search_demo.web.api import create_app

ROOT = Path(__file__).resolve().parents[1]


def run() -> tuple[dict, int]:
    counts = {"model": 0, "search": 0, "unexpected": 0}

    class Handler(BaseHTTPRequestHandler):
        def _write(self, data: dict):
            body = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.startswith("/search?"):
                counts["search"] += 1
                self._write({"results": [{
                    "url": "https://docs.python.org/3/library/asyncio.html",
                    "title": "Python asyncio documentation",
                    "content": "Python official docs", "engine": "fixture",
                }]})
            else:
                counts["unexpected"] += 1
                self.send_error(404)

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                counts["unexpected"] += 1
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
            counts["model"] += 1
            messages = request.get("messages", [])
            tool_seen = any(m.get("role") == "tool" for m in messages)
            if tool_seen:
                message = {
                    "role": "assistant",
                    "content": "A local search was completed.",
                }
                finish = "stop"
            else:
                message = {
                    "role": "assistant", "content": None,
                    "tool_calls": [{
                        "id": "call-search-fixture", "type": "function",
                        "function": {
                            "name": "search_web",
                            "arguments": json.dumps({"query": "python asyncio"}),
                        },
                    }],
                }
                finish = "tool_calls"
            self._write({
                "id": "chatcmpl-local-fixture", "object": "chat.completion",
                "created": 1781440000, "model": request.get("model", "fixture-model"),
                "choices": [{
                    "index": 0, "message": message,
                    "finish_reason": finish,
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            })

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    env = os.environ.copy()
    env.update({
        "OPENAI_MODEL": "fixture-model",
        "OPENAI_BASE_URL": url + "/v1",
        "OPENAI_API_KEY": "fixture-not-real",
        "SEARXNG_BASE_URL": url,
        "NO_PROXY": "127.0.0.1,localhost",
        "no_proxy": "127.0.0.1,localhost",
    })
    cli_ok = api_ok = False
    errors = []
    prior = {key: os.environ.get(key) for key in env if key in (
        "OPENAI_MODEL", "OPENAI_BASE_URL", "OPENAI_API_KEY",
        "SEARXNG_BASE_URL", "NO_PROXY", "no_proxy",
    )}
    try:
        subprocess_result = subprocess.run([
            sys.executable, "-m", "local_search_demo", "agent",
            "Find the official Python asyncio documentation",
            "--tool-choice", "auto", "--json",
        ], cwd=ROOT, env=env, capture_output=True, text=True, timeout=40)
        try:
            payload = json.loads(subprocess_result.stdout)
            agent = payload["agent"]
            cli_ok = (
                subprocess_result.returncode == 0
                and agent["status"] == "DONE"
                and len(agent["tool_calls"]) == 1
                and agent["tool_calls"][0]["call_id"] == "call-search-fixture"
                and agent["tool_calls"][0]["name"] == "search_web"
                and agent["tool_calls"][0]["status"] == "PASS"
            )
        except (KeyError, TypeError, ValueError):
            errors.append("CLI_JSON_OR_TRACE_INVALID")

        os.environ.update({k: env[k] for k in prior})
        app = create_app(searxng_base_url=url)
        with TestClient(app) as client:
            response = client.post(
                "/api/agent",
                json={"question": "Find official asyncio documentation"},
            )
            try:
                payload = response.json()
                agent = payload["agent"]
                api_ok = (
                    response.status_code == 200
                    and agent["status"] == "DONE"
                    and len(agent["tool_calls"]) == 1
                    and agent["tool_calls"][0]["name"] == "search_web"
                    and agent["tool_calls"][0]["call_id"] == "call-search-fixture"
                )
            except (KeyError, TypeError, ValueError):
                errors.append("API_JSON_OR_TRACE_INVALID")
    finally:
        for key, prior_value in prior.items():
            if prior_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prior_value
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)
    passed = cli_ok and api_ok and counts == {"model": 4, "search": 2, "unexpected": 0}
    report = {
        "batch": "B07",
        "kind": "ordinary_CLI_API_real_OpenAI_SDK_loopback",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if passed else "FAIL",
        "cli_agent": "PASS" if cli_ok else "FAIL",
        "api_agent": "PASS" if api_ok else "FAIL",
        "counts": counts,
        "errors": errors,
        "real_model_invoked": False,
        "key_value_recorded": False,
        "scope": "Fixture model endpoint; validates serialization and tool loop, not G4 or browser human acceptance.",
    }
    return report, 0 if passed else 2


def main() -> int:
    report, rc = run()
    output = ROOT / "reports/B07/interfaces/ci-smoke.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output)}, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
