#!/usr/bin/env python3
"""B07 explicit real-model smoke: CLI-only, env credentials, structured evidence.

This script performs real API calls ONLY when the operator invokes it.
No keys, headers or private environment values are stored in the report.
Model-controlled webpage reads are disabled by default; enabling requires the
G6 signed-off index and successful target-host direct TLS smoke.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.agent.provider import OpenAIChatProvider
from local_search_demo.agent.runner import AgentRunner
from local_search_demo.fetch.httpx_fetcher import create_http_client

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs/OPEN_VALIDATION_INDEX.md"
HTTPS_REPORT = ROOT / "reports/B06/safe-http-live.json"


def live_read_gate(*, index_file: Path = INDEX, report_file: Path = HTTPS_REPORT) -> tuple[bool, str]:
    """Operational signoff check, not a substitute for the SafePublicTransport."""
    try:
        index = index_file.read_text(encoding="utf-8")
        row = next(line for line in index.splitlines() if line.startswith("| **B06-URL-SEC-01**"))
        report = json.loads(report_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, StopIteration):
        return False, "Missing safety index or HTTPS smoke report"
    if "**PASS" not in row.split("|")[3]:
        return False, "B06-URL-SEC-01 has not been formally marked PASS"
    if report.get("status") != "PASS" or len(report.get("rows", [])) < 2:
        return False, "Pinned HTTPS target-host smoke is not PASS"
    if any(item.get("status") != "PASS" for item in report["rows"]):
        return False, "At least one public HTTPS smoke target failed"
    return True, "G6 signoff and pinned HTTPS smoke evidence present"


async def run_live(config: argparse.Namespace) -> dict:
    model = config.model or os.getenv("OPENAI_MODEL", "")
    base_url = config.base_url or os.getenv("OPENAI_BASE_URL", "")
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not model or not base_url or not api_key:
        raise ValueError("Missing OPENAI_MODEL / OPENAI_BASE_URL / OPENAI_API_KEY (stored in environment only)")
    gate_reason = "Real model URL reads disabled"
    if config.allow_live_read:
        allowed, gate_reason = live_read_gate()
        if not allowed:
            raise ValueError("Unsafe to enable real page reading: " + gate_reason)

    provider = OpenAIChatProvider(
        model=model,
        base_url=base_url,
        api_key=api_key,
        api_mode=config.api_mode,
        timeout=config.timeout,
        thinking=getattr(config, "thinking", None),
        max_tokens=getattr(config, "max_tokens", 1024),
    )
    try:
        async with create_http_client() as search_client:
            dispatcher = AgentToolDispatcher(
                client=search_client,
                mode="live",
                searxng_base_url=config.searxng_base_url,
                enable_live_reads=config.allow_live_read,
            )
            record = await AgentRunner(
                provider, dispatcher,
                timeout=config.timeout, max_rounds=config.max_rounds,
                tool_choice=config.tool_choice,
            ).run(config.question)
    finally:
        await provider.aclose()

    trace = record.agent
    # No key, authorization headers or full webpage raw HTML is written.
    return {
        "batch": "B07",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": trace.status if trace else "ERROR",
        "provider": provider.provider_name,
        "model": model,
        "api_mode": provider.api_mode,
        "thinking": provider.thinking,
        "max_tokens_per_request": provider.max_tokens,
        "model_calls": provider.call_log,
        "core_execution_evidence": dispatcher.execution_evidence,
        "tool_choice": config.tool_choice,
        "live_read_enabled": config.allow_live_read,
        "live_read_gate": gate_reason,
        "real_model_invoked": True,
        "agent_trace": trace.model_dump(mode="json") if trace else None,
        "agent_total_elapsed_ms": record.total_elapsed_ms,
        "limitations": "Real G4 PASS requires successful local search→safe read→cited answer, and human trace review.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicit B07 model API smoke; no credentials logged")
    parser.add_argument("--question", required=True)
    parser.add_argument("--model", default=None, help="Defaults to OPENAI_MODEL")
    parser.add_argument("--base-url", default=None, help="Defaults to OPENAI_BASE_URL; never include credentials in URL")
    parser.add_argument("--api-mode", default="chat_completions", choices=["chat_completions", "responses"])
    parser.add_argument("--searxng-base-url", default=os.getenv("SEARXNG_BASE_URL","http://127.0.0.1:8080"))
    parser.add_argument("--tool-choice", choices=["auto","required","none"], default="auto")
    parser.add_argument("--allow-live-read", action="store_true", help="Requires G6 PASS in index and target-host pinned HTTPS smoke PASS")
    parser.add_argument("--timeout", type=float, default=70)
    parser.add_argument("--max-rounds", type=int, default=6)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--thinking", choices=["enabled", "disabled"], default=None,
                        help="Explicit provider thinking mode; DeepSeek defaults to enabled")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/B07/agent-live.json")
    args = parser.parse_args()
    # Validation happens BEFORE any network call.
    if args.allow_live_read:
        ok, why = live_read_gate()
        if not ok:
            parser.error("B06 safety gate not passed: " + why)
    if args.api_mode != "chat_completions":
        parser.error("B07 first adapter only supports chat_completions; responses is NOT_IMPLEMENTED")
    if args.timeout <= 0 or args.max_rounds <= 0 or args.max_tokens <= 0:
        parser.error("timeout, max-rounds and max-tokens must be positive")
    if args.thinking == "enabled" and args.tool_choice == "required":
        parser.error("required is incompatible with DeepSeek thinking mode; use --thinking disabled")

    try:
        result = asyncio.run(run_live(args))
    except (ValueError, OSError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc)},ensure_ascii=False))
        return 2
    args.output.parent.mkdir(parents=True,exist_ok=True)
    # Raw traces are local and ignored by Git; restrict filesystem access too.
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    args.output.chmod(0o600)
    print(json.dumps({
        "status": result["status"], "model": result["model"],
        "tool_calls": len((result["agent_trace"] or {}).get("tool_calls",[])),
        "live_read_enabled": result["live_read_enabled"],
        "output": str(args.output),
    },ensure_ascii=False))
    return 0 if result["status"] == "DONE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
