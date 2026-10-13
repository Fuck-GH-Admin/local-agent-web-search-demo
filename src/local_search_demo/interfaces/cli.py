"""B00 entrypoint: help, offline environment checks, explicit future commands."""

import argparse
import json
from pathlib import Path

from local_search_demo import __version__
from local_search_demo.environment import environment_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local search demo (B00 baseline)")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    env = commands.add_parser("environment", help="Check imports and report the local environment offline")
    env.add_argument("--project-root", type=Path, default=Path.cwd())
    env.add_argument("--output", type=Path)
    for name, argument in [("search", "query"), ("read", "url"), ("agent", "question")]:
        child = commands.add_parser(name, help="Planned command; not implemented in B00")
        child.add_argument(argument)
        child.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "environment":
        report = environment_report(args.project_root)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0 if report["status"] == "PASS" else 1
    print(json.dumps({"command": args.command, "status": "NOT_IMPLEMENTED",
                      "batch": "B00", "message": "This functionality is scheduled for a later batch."}))
    return 2
