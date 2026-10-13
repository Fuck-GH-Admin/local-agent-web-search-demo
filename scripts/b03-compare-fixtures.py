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


def render_markdown(report: dict) -> str:
    """Human-readable parser observations, not a human quality verdict."""
    parts = [
        "# B03 固定样本解析器对比（G2 人工验收待完成）", "",
        "来源：六份合成 HTML；本报告耗时仅是单次实验，非性能基准。", "",
        "完整 raw_output 及元数据见 parser-comparison.json。", "",
    ]
    for case in report["cases"]:
        parts += [
            f"## {case['fixture_id']} ({case['category']})", "",
            "| 解析器 | 状态 | 字符 | 耗时 (ms) | 正文锚点 | 噪声锚点 |",
            "|---|---|---:|---:|---|---|",
        ]
        for entry in case["results"]:
            obs = entry["anchor_observations"]
            body = ", ".join(f"{key}: {value}" for key, value in obs["expected_body_anchors"].items()) or "—"
            noise = ", ".join(f"{key}: {value}" for key, value in obs["noise_anchors"].items()) or "—"
            parts.append(f"| {entry['name']} | {entry['status']} | {entry['chars']} | {entry['elapsed_ms']} | {body} | {noise} |")
        parts.append("")
        for entry in case["results"]:
            parts += [
                f"### {entry['name']} — {entry['status']}", "",
                "~~~~text", entry.get("text") or "(empty)", "~~~~", "",
            ]
    parts += [
        "## 人工待做", "",
        "逐条查看 18 组文字，在 manual-review.json 标注 correct / partial / noise / no_content / blocked。",
        "每一组必须给出理由；此处 PASS 只是正文非空，不等于质量正确。",
    ]
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--markdown", type=Path, default=ROOT / "reports/B03/parser-comparison.md")
    args = parser.parse_args()
    report, review = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.review.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    if not args.review.exists():
        args.review.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "cases": len(report["cases"]), "parsers_per_case": 3,
        "quality_review": review["human_review_status"],
        "output": str(args.output), "review": str(args.review), "markdown": str(args.markdown),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
