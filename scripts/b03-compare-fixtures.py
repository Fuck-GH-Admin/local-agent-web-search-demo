#!/usr/bin/env python3
"""Generate reproducible B03 parser output and unreviewed quality worksheets.

All inputs are saved synthetic HTML; this script never fetches URLs.
"""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path

from local_search_demo.parsers.comparison import compare_parsers

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"
DEFAULT_OUT = ROOT / "reports/B03/parser-comparison.json"
DEFAULT_REVIEW = ROOT / "reports/B03/manual-review.json"


def build_report() -> tuple[dict, dict]:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    cases, review_rows = [], []
    for sample in manifest:
        if sample.get("format") != "html":
            continue
        content = (FIXTURES / sample["path"]).read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != sample["sha256"]:
            raise ValueError(f"Fixture changed without updating manifest: {sample['id']}")
        html = content.decode("utf-8")
        results = compare_parsers(html, url=f"https://example.org/synthetic/{sample['id']}")
        output = []
        for entry in results:
            text = entry.text or ""
            evidence = {
                "expected_body_anchors": {a: a in text for a in sample["expected_body_anchors"]},
                "noise_anchors": {a: a in text for a in sample.get("noise_anchors", [])},
            }
            output.append({**entry.model_dump(mode="json"), "anchor_observations": evidence})
            review_rows.append({
                "case_id": sample["id"], "parser": entry.name,
                "quality": "UNREVIEWED", "reason": "",
            })
        cases.append({
            "fixture_id": sample["id"], "category": sample["category"],
            "synthetic": True, "html_sha256": digest,
            "expect_body": sample["expect_body"], "results": output,
        })
    report = {
        "batch": "B03",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": "six synthetic offline HTML fixtures",
        "manual_G2_status": "NOT_RUN",
        "cases": cases,
        "caveat": "Anchor match is only an automated observation, NOT an accuracy verdict.",
    }
    review = {
        "batch": "B03", "human_review_status": "NOT_RUN",
        "instructions": "For every row choose correct / partial / noise / no_content / blocked and describe why; do not mark PASS before reviewing raw/text fields.",
        "reviews": review_rows,
    }
    return report, review


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    args = parser.parse_args()
    report, review = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.review.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.review.exists():
        args.review.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "cases": len(report["cases"]), "parsers_per_case": 3,
        "quality_review": review["human_review_status"],
        "output": str(args.output), "review": str(args.review),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
