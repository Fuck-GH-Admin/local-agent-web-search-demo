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
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit
from uuid import uuid4

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
    private_dir = ROOT / "reports/B08/raw" / ("pages-" + uuid4().hex)
    if raw:
        private_dir.mkdir(parents=True, mode=0o700)
    for case_id,url in source_urls():
        html_path = private_dir / (case_id + ".html") if raw else None
        if html_path:
            # The Core writes the already downloaded bytes into this private
            # file; pre-create it to prevent a world-readable write window.
            html_path.touch(mode=0o600, exist_ok=False)
        try:
            record=await read_webpage(url, timeout=20, save_raw=html_path)
        except Exception as exc:
            if html_path:
                html_path.unlink(missing_ok=True)
            # Record site failures instead of losing the whole six-site batch.
            cases.append({
                "case_id": case_id, "requested_url": url,
                "observed_utc": datetime.now(timezone.utc).isoformat(),
                "fetch_status": "FAIL", "error_kind": type(exc).__name__,
                "parsers": [], "human_quality_review": "NOT_RUN",
            })
            continue
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
            target=private_dir / (case_id+".json")
            target.parent.mkdir(parents=True,exist_ok=True)
            # Never publish arbitrary webpage text from a live website.
            with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),"w",encoding="utf-8") as out:
                out.write(record.model_dump_json(indent=2)+"\n")
            outcome["private_record"]=str(target.relative_to(ROOT))
            outcome["private_record_sha256"]=hashlib.sha256(target.read_bytes()).hexdigest()
            if fetch and fetch.status == "PASS":
                outcome["private_html"]=str(html_path.relative_to(ROOT))
                outcome["html_sha256"]=hashlib.sha256(html_path.read_bytes()).hexdigest()
            else:
                html_path.unlink(missing_ok=True)
        cases.append(outcome)
        print(json.dumps({"case":case_id,"fetch":outcome["fetch_status"],"http":outcome["http_status"],
                          "parsers":[[p["name"],p["status"],p["chars"]] for p in outcome["parsers"]]}),flush=True)
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
            checks=[]
            if name == "B06_safety":
                revision=content["tested_source_commit"]
                for filename,digest in content["source_and_lock_hashes"].items():
                    original=subprocess.check_output(["git","show",revision+":"+filename],cwd=ROOT,stderr=subprocess.DEVNULL)
                    checks.append(hashlib.sha256(original).hexdigest()==digest)
                verified=status=="PASS_READY_FOR_B07" and bool(checks) and all(checks)
            else:
                revision=content["approved_evidence_commit"]
                if name == "G2":
                    bindings=[("reports/B03/parser-comparison.json",content["approved_comparison_sha256"]),
                              ("reports/B03/manual-review.json",content["approved_review_before_signoff_sha256"]),
                              ("reports/B03/quality-review.md",content["approved_quality_summary_before_signoff_sha256"])]
                elif name == "G3":
                    bindings=[("reports/B05/g3-local-review.md",content["approved_review_sha256"]),
                              ("reports/B05/browser-observations.json",content["approved_browser_observations_before_signoff_sha256"]),
                              ("reports/B05/acceptance.json",content["approved_acceptance_before_signoff_sha256"])]
                    checks.extend(hashlib.sha256((ROOT/x["file"]).read_bytes()).hexdigest()==x["sha256"] for x in content["screenshots"])
                else:
                    bindings=[(x["file"],x["approved_sha256"]) for x in content["approved_evidence"]]
                    # Raw model traces are intentionally absent from CI/cloud.
                    # If local originals exist, check them without publishing.
                    checks.extend(hashlib.sha256((ROOT/x["file_local_only"]).read_bytes()).hexdigest()==x["sha256"]
                                  for x in content["approved_local_trace_hashes"] if (ROOT/x["file_local_only"]).exists())
                for filename,digest in bindings:
                    matched=False
                    for commit in [revision,revision+"^"]:
                        original=subprocess.check_output(["git","show",commit+":"+filename],cwd=ROOT,stderr=subprocess.DEVNULL)
                        if hashlib.sha256(original).hexdigest()==digest:
                            matched=True;break
                    checks.append(matched)
                verified=status=="APPROVED" and content.get("signed_by")=="user" and bool(bindings) and all(checks)
            results[name]={"present":True,"reported_status":status,"verified":verified,"binding_checks":len(checks)}
        except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError):
            results[name]={"present":(ROOT/path).exists(),"reported_status":"UNVERIFIED","verified":False}
    return results


def main() -> int:
    parser=argparse.ArgumentParser(description="B08 evidence collection, never an automatic G5 signoff")
    parser.add_argument("--live",action="store_true",help="Make fresh HTTP requests to at least five real sites")
    parser.add_argument("--save-private",action="store_true",help="Write full page/parser records to gitignored 0600 raw directory")
    parser.add_argument("--output",type=Path,default=ROOT/"reports/B08/observations.json")
    args=parser.parse_args()
    if args.save_private and not args.live:
        parser.error("--save-private requires --live")

    check_dir=ROOT/"reports/B08/raw"/("checks-"+uuid4().hex)
    check_dir.mkdir(parents=True,mode=0o700)
    checks=[run_cmd(["uv","run","--locked","pytest","-q","--junitxml="+str(check_dir/"pytest.xml")],timeout=240)]
    # Historical gate reports remain immutable; archive this run's fresh
    # artifacts and restore only the exact files touched by these scripts.
    for script,filename in [("b04-cli-smoke.py","reports/B04/cli-smoke.json"),
                            ("b05-api-parity.py","reports/B05/api-tests.json"),
                            ("b06-offline-tool-smoke.py","reports/B06/tool-loop-tests.json"),
                            ("b07-interfaces-smoke.py","reports/B07/interfaces/ci-smoke.json")]:
        target=ROOT/filename
        previous=target.read_bytes() if target.exists() else None
        try:
            result=run_cmd(["uv","run","--locked","python","scripts/"+script])
            if target.exists() and target.read_bytes()!=previous:
                saved=check_dir/Path(filename).name
                shutil.copy2(target,saved)
                result["private_artifact"]=str(saved.relative_to(ROOT))
            checks.append(result)
        finally:
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(previous)
    pages=asyncio.run(capture_live_pages(raw=args.save_private)) if args.live else []
    report={
        "batch":"B08","generated_utc":datetime.now(timezone.utc).isoformat(),
        "mode":"EXPLICIT_LIVE" if args.live else "OFFLINE_ONLY",
        "private_checks_directory":str(check_dir.relative_to(ROOT)),
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
    passed=all(x["status"]=="PASS" for x in checks) and all(x["verified"] for x in report["prior_evidence"].values())
    live_ready = not args.live or (
        len(pages) >= 5
        and len({urlsplit(x["requested_url"]).hostname for x in pages}) >= 5
        and sum(x["fetch_status"] == "PASS" for x in pages) >= 5
    )
    report["status"]=(
        "PRECHECK_PASS_G5_NOT_RUN" if passed and live_ready
        else "PRECHECK_PARTIAL_G5_NOT_RUN"
    )
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"fresh_sites":report["different_real_hosts"],
                      "G5":"NOT_RUN","output":str(args.output)},ensure_ascii=False))
    return 0 if passed and live_ready else 2


if __name__=="__main__":
    raise SystemExit(main())
