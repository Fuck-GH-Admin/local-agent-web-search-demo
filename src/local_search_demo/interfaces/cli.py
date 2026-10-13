"""CLI: B01 local SearXNG search plus unchanged B00 environment command."""
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

    for name, argument in [("read", "url"), ("agent", "question")]:
        child = commands.add_parser(name, help="Planned for a later batch")
        child.add_argument(argument)
        child.add_argument("--json", action="store_true")
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
    print(json.dumps({
        "command": args.command,
        "status": "NOT_IMPLEMENTED",
        "batch": "B01",
        "message": "This functionality is scheduled for a later batch.",
    }))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
