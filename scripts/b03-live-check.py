#!/usr/bin/env python3
"""Check evidence completeness/bindings; never infer a quality label."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", type=Path, default=ROOT / "reports/B03/live")
    args = parser.parse_args()
    root = args.report_dir
    report = json.loads((root / "parser-comparison.json").read_text())
    review = json.loads((root / "quality-review.json").read_text())
    assert review["review_status"] == "REVIEWED", "Content review has not been recorded"
    assert review["comparison_report_sha256"] == hashlib.sha256((root / "parser-comparison.json").read_bytes()).hexdigest()
    cases = report["cases"]
    assert len({urlsplit(c["requested_url"]).hostname for c in cases}) >= 5
    assert sum(c["fetch"]["status"] == "PASS" for c in cases) >= 5
    expected = {(c["case_id"], p["name"]) for c in cases for p in c["parsers"]}
    rows = review["reviews"]
    assert len(rows) == len(expected) == 3 * len(cases)
    assert {(r["case_id"], r["parser"]) for r in rows} == expected
    for row in rows:
        assert row["quality"] in {"correct", "partial", "noise", "no_content", "blocked"}
        assert len(row["reason"].strip()) >= 20
    verified_raw = 0
    for case in cases:
        source = root / "raw" / f"{case['case_id']}.html"
        output = root / "raw" / f"{case['case_id']}.json"
        if source.exists() and output.exists():
            assert hashlib.sha256(source.read_bytes()).hexdigest() == case["html_sha256"]
            assert hashlib.sha256(output.read_bytes()).hexdigest() == case["full_parser_output_sha256"]
            full = json.loads(output.read_text())["results"]
            for actual, summarized in zip(full, case["parsers"], strict=True):
                assert actual["name"] == summarized["name"]
                for field in ("text", "raw_output"):
                    value = actual[field]
                    digest = hashlib.sha256(value.encode()).hexdigest() if value is not None else None
                    assert digest == summarized[f"{field}_sha256"]
            verified_raw += 1
    print(json.dumps({"status": "PASS", "cases": len(cases), "reviews": len(rows),
                      "quality_counts": dict(Counter(r["quality"] for r in rows)),
                      "local_raw_verified": verified_raw,
                      "note": "Completeness/hash check only; quality labels were supplied by the recorded reviewer."}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
