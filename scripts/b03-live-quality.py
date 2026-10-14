#!/usr/bin/env python3
"""Explicit real-web capture for B03-LIVE-02. No automatic quality labels.

One HTTPX download per page, same bytes for all three adapters. Full source and
parser output stay in ignored raw/; shareable report contains hashes/metadata.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess

from local_search_demo.fetch.httpx_fetcher import HTMLFetcher, create_http_client, save_html
from local_search_demo.parsers.comparison import compare_downloaded

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ("python-article", "普通介绍文章", "https://www.python.org/doc/essays/blurb/"),
    ("wikipedia-article", "百科/导航密集", "https://en.wikipedia.org/wiki/Web_scraping"),
    ("mdn-documentation", "技术文档/代码", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Redirections"),
    ("gnu-chinese", "中文长文章", "https://www.gnu.org/philosophy/free-sw.zh-cn.html"),
    ("kubernetes-documentation", "技术文档/目录", "https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/"),
    ("diagrams-spa", "浏览器应用/SPA", "https://app.diagrams.net/"),
]


def digest(text: str | bytes | None) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8") if isinstance(text, str) else text).hexdigest()


async def collect(output: Path) -> dict:
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    cases, reviews = [], []
    async with create_http_client(trust_env=True) as client:
        for case_id, category, url in TARGETS:
            started = datetime.now(timezone.utc).isoformat()
            doc = await HTMLFetcher(client).fetch(url, timeout=20.0)
            if doc.result.status == "PASS":
                save_html(doc, raw / f"{case_id}.html")
            results = compare_downloaded(doc)
            full = {"case_id": case_id, "results": [p.model_dump(mode="json") for p in results]}
            (raw / f"{case_id}.json").write_text(json.dumps(full, ensure_ascii=False, indent=2) + "\n")
            parser_rows = []
            for entry in results:
                item = entry.model_dump(mode="json", exclude={"text", "raw_output"})
                item.update(text_sha256=digest(entry.text), raw_output_sha256=digest(entry.raw_output))
                parser_rows.append(item)
                reviews.append({"case_id": case_id, "parser": entry.name, "quality": "UNREVIEWED", "reason": ""})
            fetch = doc.result.model_dump(mode="json")
            fetch["html_path"] = f"raw/{case_id}.html" if doc.html_bytes is not None else None
            cases.append({
                "case_id": case_id, "category": category, "synthetic": False,
                "requested_url": url, "observed_utc": started,
                "fetch": fetch, "html_sha256": digest(doc.html_bytes),
                "full_parser_output_sha256": digest((raw / f"{case_id}.json").read_bytes()),
                "parsers": parser_rows,
            })
            print(json.dumps({"case": case_id, "fetch": fetch["status"], "http": fetch["http_status"],
                              "parsers": [[p.name, p.status, p.chars] for p in results]}, ensure_ascii=False), flush=True)
    report = {
        "validation_id": "B03-LIVE-02", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "implementation_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": platform.python_version(), "platform": platform.platform(),
        "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "source_hashes": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in
                          [ROOT / "src/local_search_demo/fetch/httpx_fetcher.py", *sorted((ROOT / "src/local_search_demo/parsers").glob("*.py"))]},
        "mode": "explicit HTTPX live capture; host proxy inherited; no browser fetching",
        "quality_review_status": "NOT_RUN", "cases": cases,
        "limitation": "Purposively selected pages; no general internet accuracy or performance ranking. Full HTML/output stays local in ignored raw/.",
    }
    (output / "parser-comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    review_path = output / "quality-review.json"
    if not review_path.exists():
        review_path.write_text(json.dumps({
            "validation_id": "B03-LIVE-02", "reviewer": None, "review_status": "NOT_RUN",
            "instructions": "Read original HTML and raw/text/title/metadata of every parser, then explain labels. Network failure is blocked, not successful extraction.",
            "reviews": reviews,
        }, ensure_ascii=False, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/B03/live")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Do not silently overwrite a previously reviewed capture.
    if (args.output_dir / "parser-comparison.json").exists():
        parser.error("Use a new --output-dir to preserve the previous live capture")
    report = asyncio.run(collect(args.output_dir))
    return 0 if sum(c["fetch"]["status"] == "PASS" for c in report["cases"]) >= 5 else 2


if __name__ == "__main__":
    raise SystemExit(main())
