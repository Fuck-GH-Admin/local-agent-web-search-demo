#!/usr/bin/env python3
"""B08 final acceptance *evidence collector*, not an automatic G5 signoff.

Default is offline-only and does not invoke paid models.
--live explicitly fetches fresh pages from six previously reviewed B03 real
websites, storing only derived metadata publicly and private full payloads in
Git-ignored reports/B08/raw. Human content review is still required.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
from urllib.parse import urlsplit

from local_search_demo.pipeline.reader import read_webpage

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(args: list[str], timeout: int = 180) -> dict:
    started = time.perf_counter()
    try:
        process = subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
        return {
            "command": args, "status": "PASS" if process.returncode == 0 else "FAIL",
            "returncode": process.returncode,
            "elapsed_ms": round((time.perf_counter()-started)*1000,3),
            "summary": (process.stdout.splitlines()[-1] if process.stdout else "")[:400],
            "stderr_excerpt": (process.stderr.splitlines()[-1] if process.stderr else "")[:220],
        }
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {"command": args, "status": "BLOCKED",
                "error": type(exc).__name__}


def sha(text: str | None) -> str | None:
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text is not None else None


def source_urls() -> list[tuple[str, str]]:
    """Reuse actual named real-site sampling targets; DO NOT reuse old results."""
    source = json.loads((ROOT / "reports/B03/live/parser-comparison.json").read_text())
    result = [(row["case_id"],row["requested_url"]) for row in source["cases"]]
    domains = {urlsplit(url).hostname for _,url in result}
    if len(domains) < 5:
        raise ValueError("B08 requires at least five distinct real sites")
    return result


async def capture_live_pages(*, raw: bool) -> list[dict]:
    cases=[]
    for case_id,url in source_urls():
        record=await read_webpage(url)
        fetch=record.fetch
        outcome={
            "case_id":case_id,
            "requested_url":url,
            "observed_utc":datetime.now(timezone.utc).isoformat(),
            "fetch_status":fetch.status if fetch else "NOT_RUN",
            "http_status":fetch.http_status if fetch else None,
            "final_url":fetch.url_final if fetch else None,
            "bytes":fetch.bytes if fetch else None,
            "fetch_elapsed_ms":fetch.elapsed_ms if fetch else None,
            "fetch_error":fetch.error.kind if fetch and fetch.error else None,
            "selected_parser":record.selected_parser,
            "selection_reason":record.selection_reason,
            "selected_text_sha256":sha(record.selected_text),
            "parsers":[{
                "name":p.name,"status":p.status,
                "chars":p.chars,"elapsed_ms":p.elapsed_ms,
                "title":p.title,
                "error_kind":p.error.kind if p.error else None,
                "text_sha256":sha(p.text),
                "raw_sha256":sha(p.raw_output),
            } for p in record.parsers],
            "human_quality_review":"NOT_RUN",
        }
        if raw:
            target=ROOT / "reports/B08/raw" / (case_id+".json")
            target.parent.mkdir(parents=True,exist_ok=True)
            # Never publish arbitrary webpage text from a live website.
            with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),"w",encoding="utf-8") as out:
                out.write(record.model_dump_json(indent=2)+"\n")
            outcome["private_record"]="reports/B08/raw/"+case_id+".json"
        cases.append(outcome)
    return cases


def validate_prior_evidence() -> dict:
    """Strictly check prior signoffs, without converting them into G5 PASS."""
    files={
        "G2":"reports/B03/g2-signoff.json",
        "G3":"reports/B05/g3-signoff.json",
        "B06_safety":"reports/B06/readiness-audit/acceptance.json",
        "G4":"reports/B07/validation/g4-signoff.json",
    }
    results={}
    for name,path in files.items():
        try:
            content=json.loads((ROOT/path).read_text(encoding="utf-8"))
            status=content.get("status",content.get("gate_result"))
            results[name]={"present":True,"reported_status":status}
        except (OSError,ValueError):
            results[name]={"present":False,"reported_status":"MISSING"}
    return results


def main() -> int:
    parser=argparse.ArgumentParser(description="B08 evidence collection, never an automatic G5 signoff")
    parser.add_argument("--live",action="store_true",help="Make fresh HTTP requests to at least five real sites")
    parser.add_argument("--save-private",action="store_true",help="Write full page/parser records to gitignored 0600 raw directory")
    parser.add_argument("--output",type=Path,default=ROOT/"reports/B08/observations.json")
    args=parser.parse_args()
    if args.save_private and not args.live:
        parser.error("--save-private requires --live")

    checks=[
        run_cmd(["uv","run","--locked","pytest","-q"],timeout=240),
        run_cmd(["uv","run","--locked","python","scripts/b04-cli-smoke.py"]),
        run_cmd(["uv","run","--locked","python","scripts/b05-api-parity.py"]),
        run_cmd(["uv","run","--locked","python","scripts/b06-offline-tool-smoke.py"]),
        run_cmd(["uv","run","--locked","python","scripts/b07-interfaces-smoke.py"]),
    ]
    pages=asyncio.run(capture_live_pages(raw=args.save_private)) if args.live else []
    report={
        "batch":"B08","generated_utc":datetime.now(timezone.utc).isoformat(),
        "mode":"EXPLICIT_LIVE" if args.live else "OFFLINE_ONLY",
        "platform":platform.platform(),"python":sys.version.split()[0],
        "prior_evidence":validate_prior_evidence(),
        "commands":checks,
        "real_pages":pages,
        "fresh_real_page_count":len(pages),
        "different_real_hosts":len({urlsplit(x["requested_url"]).hostname for x in pages}),
        "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "G5":"NOT_RUN",
        "real_model_rerun":"NOT_RUN",
        "human_parser_review":"NOT_RUN",
        "note":"B08 G5 cannot be signed without manual page-quality review, real Agent rerun, environment/resource inspection and unresolved-gate review.",
    }
    passed=all(x["status"]=="PASS" for x in checks)
    report["status"]="PRECHECK_PASS_G5_NOT_RUN" if passed else "PRECHECK_FAILED_G5_NOT_RUN"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"fresh_sites":report["different_real_hosts"],
                      "G5":"NOT_RUN","output":str(args.output)},ensure_ascii=False))
    return 0 if passed else 2


if __name__=="__main__":
    raise SystemExit(main())
