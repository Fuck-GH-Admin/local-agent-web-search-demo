#!/usr/bin/env python3
"""Repeat B02 acceptance and save actual pytest cases and optional live results."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from local_search_demo.environment import environment_report

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/B02"


def save(name, data):
    (OUTPUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Also attempt the two nonblocking public HTML downloads")
    parser.add_argument("--save-html", action="store_true", help="Save already-downloaded HTML to the ignored raw directory")
    args = parser.parse_args()
    if args.save_html and not args.live:
        parser.error("--save-html requires --live")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    commands = [
        ["uv", "lock", "--check"],
        ["uv", "pip", "check", "--python", sys.executable],
        [sys.executable, "-m", "pytest", "-q", "--junitxml=reports/B02/pytest.xml"],
    ]
    checks = []
    logs = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        checks.append({"command": command, "exit_code": result.returncode,
                       "status": "PASS" if result.returncode == 0 else "FAIL"})
        logs.append("$ " + " ".join(command) + "\n" + result.stdout + f"\nexit_code={result.returncode}\n")
        if "pytest" in command:
            (OUTPUT / "test-summary.txt").write_text(result.stdout, encoding="utf-8")
        print(checks[-1]["status"], " ".join(command), flush=True)
    (OUTPUT / "verification-checks.txt").write_text("\n".join(logs), encoding="utf-8")
    cases = []
    if checks[-1]["status"] == "PASS":
        for case in ET.parse(OUTPUT / "pytest.xml").getroot().iter("testcase"):
            state = ("FAIL" if case.find("failure") is not None or case.find("error") is not None
                     else "SKIPPED" if case.find("skipped") is not None else "PASS")
            cases.append({"module": case.attrib["classname"], "name": case.attrib["name"],
                          "status": state, "elapsed_ms": round(float(case.attrib["time"]) * 1000, 3)})
    offline_pass = all(c["status"] == "PASS" for c in checks) and bool(cases) and all(c["status"] == "PASS" for c in cases)
    live_status = "NOT_RUN"
    if args.live:
        command = [sys.executable, "scripts/b02-live-smoke.py"]
        if args.save_html:
            command.append("--save-html")
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (OUTPUT / "live-command.txt").write_text("$ " + " ".join(command) + "\n" + result.stdout + f"\nexit_code={result.returncode}\n", encoding="utf-8")
        if result.returncode in (0, 2):
            live_status = json.loads((OUTPUT / "live-smoke.json").read_text(encoding="utf-8"))["status"]
        else:
            live_status = "LIVE_ERROR"
    inventory = environment_report(ROOT)
    inventory["batch"] = "B02"
    inventory["network_tests"] = live_status
    save("environment.json", inventory)
    save("fetch-tests.json", {
        "batch": "B02", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "OFFLINE_PASS" if offline_pass else "FAIL", "live_site_status": live_status,
        "source": "Actual target-host pytest including loopback HTTP server traffic",
        "implementation_sha": inventory["project"]["revision"], "branch": inventory["project"]["branch"],
        "checks": checks,
        "pytest": {"passed": sum(c["status"] == "PASS" for c in cases),
                   "failed": sum(c["status"] == "FAIL" for c in cases),
                   "skipped": sum(c["status"] == "SKIPPED" for c in cases)},
        "fetch_case_count": sum("httpx_fetcher" in c["module"] or "fetch_http_local" in c["module"] for c in cases),
        "cases": cases, "article_extraction": "NOT_RUN", "model_calls": "NOT_RUN",
    })
    print(f"B02: {'OFFLINE_PASS' if offline_pass else 'FAIL'}; live: {live_status}; {len(cases)} cases")
    return 0 if offline_pass and live_status != "LIVE_ERROR" else 1


if __name__ == "__main__":
    raise SystemExit(main())
