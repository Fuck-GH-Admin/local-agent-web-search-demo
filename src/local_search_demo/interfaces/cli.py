"""Shared B07 CLI: environment, search, read and model Agent Core."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from local_search_demo import __version__
from local_search_demo.environment import environment_report
from local_search_demo.schemas import ExperimentRecord
from local_search_demo.search.searxng import search_web
from local_search_demo.pipeline.reader import read_webpage
from local_search_demo.fetch.httpx_fetcher import create_http_client
from local_search_demo.agent.service import AgentConfigurationError, execute_agent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local search demo (B01 SearXNG)")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    env = commands.add_parser("environment", help="Report installed dependencies offline")
    env.add_argument("--project-root", type=Path, default=Path.cwd())
    env.add_argument("--output", type=Path)

    search = commands.add_parser("search", help="Query local SearXNG; no LLM needed")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--language", default=None)
    search.add_argument("--time-range", choices=["day", "week", "month", "year"])
    search.add_argument("--base-url", default=None, help="Defaults to SEARXNG_BASE_URL")
    search.add_argument("--timeout", type=float, default=10.0)
    search.add_argument("--json", action="store_true", help="Print full structured experiment")
    search.add_argument("--output", type=Path, help="Save full structured experiment JSON")

    read = commands.add_parser("read", help="Download HTML once, compare 3 parsers, choose a candidate")
    read.add_argument("url")
    read.add_argument("--timeout", type=float, default=8.0)
    read.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)
    read.add_argument("--save-html", type=Path, help="Optionally save original HTML bytes")
    read.add_argument("--json", action="store_true", help="Print full experiment including 3 raw results")
    read.add_argument("--output", type=Path, help="Write full experiment JSON")
    agent = commands.add_parser("agent", help="Run real local-search Agent using configured model")
    agent.add_argument("question")
    agent.add_argument("--json", action="store_true")
    agent.add_argument("--output", type=Path)
    agent.add_argument("--model", default=None)
    agent.add_argument("--base-url", default=None)
    agent.add_argument("--searxng-base-url", default=os.getenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080"))
    agent.add_argument("--thinking", choices=["enabled", "disabled"], default="disabled")
    agent.add_argument("--max-tokens", type=int, default=1024)
    agent.add_argument("--tool-choice", choices=["auto", "required", "none"], default="auto")
    agent.add_argument("--max-rounds", type=int, default=6)
    agent.add_argument("--timeout", type=float, default=70)
    agent.add_argument("--allow-live-read", action="store_true",
                       help="Explicit opt-in; requires signed B06 URL safety evidence")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "environment":
        report = environment_report(args.project_root)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0 if report["status"] == "PASS" else 1
    if args.command == "search":
        base_url = args.base_url or os.getenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        result = asyncio.run(search_web(
            args.query, base_url=base_url, limit=args.limit,
            language=args.language, time_range=args.time_range,
            timeout=args.timeout,
        ))
        record = ExperimentRecord(
            mode="search", query=args.query, search=result,
            total_elapsed_ms=result.elapsed_ms,
        )
        payload = record.model_dump_json(indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        if args.json:
            print(payload, end="")
        else:
            print(f"Search status: {result.status} | {len(result.items)} results | {result.elapsed_ms}ms")
            for item in result.items:
                print(f"  {item.rank}. {item.title or '(untitled)'}")
                print(f"     {item.url} [{', '.join(item.engines)}]")
                if item.snippet:
                    print(f"     {item.snippet[:180]}")
            for error in result.errors:
                print(f"  ! {error.kind}: {error.message}")
        return 0 if result.status in ("PASS", "EMPTY") else 1
    if args.command == "read":
        record = asyncio.run(read_webpage(
            args.url, timeout=args.timeout, max_bytes=args.max_bytes,
            save_raw=args.save_html,
        ))
        payload = record.model_dump_json(indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        if args.json:
            print(payload, end="")
        else:
            fetch_status = record.fetch.status if record.fetch else "NOT_RUN"
            print(f"Fetch: {fetch_status} | HTTP: {record.fetch.http_status if record.fetch else None}")
            for parser_result in record.parsers:
                print(f"  {parser_result.name}: {parser_result.status}, "
                      f"chars={parser_result.chars}, elapsed={parser_result.elapsed_ms}ms")
            print(f"Chosen: {record.selected_parser or '(none)'}")
            print(record.selection_reason or "")
            if record.selected_text:
                print("\n" + record.selected_text)
            elif record.fetch and record.fetch.error:
                print(f"  ! {record.fetch.error.kind}: {record.fetch.error.message}")
        return 0 if record.fetch and record.fetch.status == "PASS" and record.selected_parser else 1
    if args.command == "agent":
        async def run_agent_command():
            async with create_http_client() as client:
                return await execute_agent(
                    args.question, search_client=client,
                    searxng_base_url=args.searxng_base_url,
                    model=args.model, base_url=args.base_url,
                    thinking=args.thinking, max_tokens=args.max_tokens,
                    tool_choice=args.tool_choice, allow_live_read=args.allow_live_read,
                    timeout=args.timeout, max_rounds=args.max_rounds,
                )

        try:
            record = asyncio.run(run_agent_command())
        except AgentConfigurationError as exc:
            print(json.dumps({"mode": "agent", "status": "BLOCKED", "reason": str(exc)},
                             ensure_ascii=False))
            return 2
        payload = record.model_dump_json(indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
            args.output.chmod(0o600)
        if args.json:
            print(payload, end="")
        else:
            print(f"Agent: {record.agent.status} | rounds={record.agent.rounds} "
                  f"| tool_calls={len(record.agent.tool_calls)}")
            print(record.agent.answer or record.agent.error or "(no final answer)")
            for url in record.agent.cited_urls:
                print(f"  source: {url}")
            for url in record.agent.unverified_citations:
                print(f"  ! unverified citation: {url}")
        return 0 if record.agent and record.agent.status == "DONE" else 1
    print(json.dumps({
        "command": args.command,
        "status": "NOT_IMPLEMENTED",
        "batch": "B04",
        "message": "This functionality is scheduled for a later batch.",
    }))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
