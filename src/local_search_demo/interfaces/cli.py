"""B00 command-line skeleton: real implementations arrive in B01/B04/B07."""
from __future__ import annotations

import argparse
from importlib import metadata
import json
import platform
import sys

from local_search_demo.config import DemoConfig


PACKAGES = ["httpx", "trafilatura", "readability-lxml", "selectolax", "openai", "fastapi", "uvicorn", "pydantic", "pytest"]


def doctor() -> dict:
    deps = {}
    for package in PACKAGES:
        try:
            deps[package] = {"status": "installed", "version": metadata.version(package)}
        except metadata.PackageNotFoundError:
            deps[package] = {"status": "missing", "version": None}
    return {
        "phase": "B00",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "dependencies": deps,
        "configuration": DemoConfig.from_env().safe_diagnostic(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Agent Web Search demo (B00 scaffold)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Report local package availability; no network requests")
    search = sub.add_parser("search", help="SearXNG search (B01/B04, not yet implemented)")
    search.add_argument("query")
    read = sub.add_parser("read", help="HTTPX + parsers (B04, not yet implemented)")
    read.add_argument("url")
    agent = sub.add_parser("agent", help="Model tool calling (B07, not yet implemented)")
    agent.add_argument("question")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        print(json.dumps(doctor(), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps({"status": "not_implemented", "phase": "B00", "command": args.command}, ensure_ascii=False))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
