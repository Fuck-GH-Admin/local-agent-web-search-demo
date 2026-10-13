#!/usr/bin/env python3
"""Run the documented G0 checks and preserve their actual output."""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(ROOT / ".venv/bin/python")


def main():
    output = ROOT / "reports/B00"
    output.mkdir(parents=True, exist_ok=True)
    commands = [
        ["uv", "--version"],
        ["uv", "lock", "--check"],
        ["uv", "pip", "check", "--python", PYTHON],
        [PYTHON, "scripts/restore_upstreams.py"],
        [PYTHON, "-m", "local_search_demo", "--help"],
        [str(ROOT / ".venv/bin/local-search-demo"), "--help"],
        [PYTHON, "-m", "local_search_demo", "environment", "--output", "reports/B00/environment.json"],
        [PYTHON, "-m", "pytest", "-q", "--junitxml=reports/B00/pytest.xml"],
    ]
    checks, logs = [], []
    for command in commands:
        started = time.perf_counter()
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check = {"command": command, "exit_code": result.returncode,
                 "status": "PASS" if result.returncode == 0 else "FAIL",
                 "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)}
        checks.append(check)
        logs.append("$ " + " ".join(command) + "\n" + result.stdout + f"\nexit_code={result.returncode}\n")
        print(f"{check['status']}: {' '.join(command[1:] if command[0] == PYTHON else command)}", flush=True)
    (output / "test-summary.txt").write_text("\n".join(logs), encoding="utf-8")
    report = {"batch": "B00", "timestamp": datetime.now(timezone.utc).isoformat(), "checks": checks,
              "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"}
    (output / "checks.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
