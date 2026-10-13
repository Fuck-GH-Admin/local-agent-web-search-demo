#!/usr/bin/env python3
"""G2 worksheet completeness check; never substitutes for actual quality judgment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED = {"correct", "partial", "noise", "no_content", "blocked"}


def check(report: dict, review: dict) -> list[str]:
    errors: list[str] = []
    cases = report.get("cases", [])
    expected = {
        (case["fixture_id"], p["name"])
        for case in cases for p in case["results"]
    }
    rows = review.get("reviews", [])
    seen = set()
    for row in rows:
        key = (row.get("case_id"), row.get("parser"))
        if key in seen:
            errors.append(f"duplicate {key}")
        seen.add(key)
        if key not in expected:
            errors.append(f"unexpected case/parser {key}")
        if row.get("quality") not in ALLOWED:
            errors.append(f"unreviewed or invalid label {key}")
        if not str(row.get("reason", "")).strip():
            errors.append(f"missing reason {key}")
    missing = expected - seen
    if missing:
        errors.append(f"missing review rows: {sorted(missing)}")
    if review.get("human_review_status") != "REVIEWED":
        errors.append("human_review_status must be REVIEWED after manual assessment")
    if len(cases) != 6 or len(expected) != 18:
        errors.append("unexpected fixture/parser count")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Validate G2 worksheet completeness, not content accuracy")
    parser.add_argument("--comparison", type=Path, default=root / "reports/B03/parser-comparison.json")
    parser.add_argument("--review", type=Path, default=root / "reports/B03/manual-review.json")
    args = parser.parse_args()
    report = json.loads(args.comparison.read_text(encoding="utf-8"))
    reviews = json.loads(args.review.read_text(encoding="utf-8"))
    errors = check(report, reviews)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("Worksheet COMPLETE (18 reviewed). G2 signoff must still inspect content and evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
