#!/usr/bin/env python3
"""Evidence-only G0 verifier. Runs without any optional demo dependencies.

It never installs packages, downloads source, contacts providers or reads API keys.
Run after `bash scripts/clone-upstream.sh` and `pip install -e '.[dev]'`.
"""
from __future__ import annotations

from importlib import metadata, import_module
from pathlib import Path
import json
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ["searxng", "httpx", "trafilatura", "selectolax", "python-readability", "openai-python"]
PACKAGES = ["httpx", "trafilatura", "readability-lxml", "selectolax", "openai", "fastapi", "uvicorn", "pydantic", "pytest"]
IMPORT_MODULES = {
    "httpx": "httpx",
    "trafilatura": "trafilatura",
    "readability-lxml": "readability",
    "selectolax": "selectolax.lexbor",
    "openai": "openai",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "pytest": "pytest",
}


def main() -> int:
    shas = {}
    for name in UPSTREAM:
        path = ROOT / ".references" / "upstream" / name
        if not (path / ".git").exists():
            shas[name] = None
            continue
        run = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, capture_output=True)
        sha = run.stdout.strip()
        shas[name] = sha if run.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha) else None
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None

    imports = {}
    for package, module in IMPORT_MODULES.items():
        try:
            import_module(module)
            imports[package] = {"status": "PASS"}
        except Exception as exc:
            imports[package] = {
                "status": "FAIL",
                "exception": type(exc).__name__,
                "detail": str(exc)[:200],
            }
    imports_ok = all(v["status"] == "PASS" for v in imports.values())

    missing_repos = [k for k, v in shas.items() if v is None]
    missing_packages = [k for k, v in versions.items() if v is None]
    commands = {}
    for name, args, expected in [
        ("pip_check", [sys.executable, "-m", "pip", "check"], 0),
        ("pytest", [sys.executable, "-m", "pytest", "-q"], 0),
        ("cli_help", [sys.executable, "-m", "local_search_demo", "--help"], 0),
        ("cli_doctor", [sys.executable, "-m", "local_search_demo", "doctor"], 0),
        ("search_stub", [sys.executable, "-m", "local_search_demo", "search", "test"], 3),
    ]:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=120)
        commands[name] = {
            "command": " ".join(args[1:]),
            "exit_code": result.returncode,
            "expected_exit": expected,
            "status": "PASS" if result.returncode == expected else "FAIL",
            "stdout_tail": result.stdout[-500:],
            "stderr_tail": result.stderr[-500:],
        }
    commands_ok = all(item["status"] == "PASS" for item in commands.values())
    status = ("BLOCKED_LOCAL" if missing_repos or missing_packages
              else "FAIL" if not commands_ok or not imports_ok
              else "PASS")
    report = {
        "gate": "G0", "status": status,
        "python": sys.version.split()[0], "platform": platform.platform(),
        "upstream_shas": shas, "package_versions": versions,
        "missing_upstream": missing_repos, "missing_packages": missing_packages,
        "imports": imports, "commands": commands,
        "note": "G0 PASS requires cloned upstream, all declared packages, and passing local tests/CLI checks. No network search is asserted.",
    }
    target = ROOT / "reports" / "B00" / "g0-local-check.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if status == "PASS":
        frozen = subprocess.run([sys.executable, "-m", "pip", "freeze"], cwd=ROOT, capture_output=True, text=True)
        if frozen.returncode == 0:
            (target.parent / "requirements-resolved.txt").write_text(frozen.stdout, encoding="utf-8")
    print(json.dumps({"gate": "G0", "status": status, "missing_upstream": missing_repos,
                      "missing_packages": missing_packages, "imports_passed": imports_ok,
                      "commands_passed": commands_ok}, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
