#!/usr/bin/env python3
"""Read-only local diagnostics for B00-B08.

Only collects an allowlist of environment data. No secrets, tokens, proxy URLs,
hostname, private addresses, or arbitrary environment variables are recorded.
No outbound network probes unless --network is explicitly supplied.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("httpx", "trafilatura", "readability-lxml", "selectolax",
            "openai", "fastapi", "uvicorn", "pydantic", "pytest")
UPSTREAM = ("searxng", "httpx", "trafilatura", "selectolax",
            "python-readability", "openai-python")


def run_status(argv: list[str], timeout: int = 8, show_version: bool = False) -> dict:
    if shutil.which(argv[0]) is None:
        return {"status": "missing"}
    try:
        proc = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except OSError as exc:
        return {"status": "error", "exception": type(exc).__name__}
    result = {"status": "ok" if proc.returncode == 0 else "failed",
              "exit_code": proc.returncode}
    if show_version and proc.returncode == 0:
        result["version"] = proc.stdout.strip().splitlines()[0][:120] if proc.stdout.strip() else None
    # Do not include stderr or arbitrary command outputs.
    return result


def local_ports() -> dict:
    result = {}
    for label, port in (("searxng", 8080), ("webui", 8765)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            try:
                listening = sock.connect_ex(("127.0.0.1", port)) == 0
            except OSError:
                listening = False
        result[label] = {"port": port, "listening": listening}
    return result


def upstream_shas() -> dict:
    result = {}
    for name in UPSTREAM:
        path = ROOT / ".references" / "upstream" / name
        if not (path / ".git").exists():
            result[name] = None
            continue
        try:
            p = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=6,
            )
            sha = p.stdout.strip()
            result[name] = sha if p.returncode == 0 and len(sha) == 40 and all(c in "0123456789abcdef" for c in sha) else None
        except (OSError, subprocess.TimeoutExpired):
            result[name] = None
    return result


def git_snapshot() -> dict:
    if not (ROOT / ".git").exists():
        return {"is_git_checkout": False}
    try:
        def git(*args: str) -> str:
            p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=6)
            return p.stdout.strip() if p.returncode == 0 else ""
        return {"is_git_checkout": True, "branch": git("branch", "--show-current"),
                "head": git("rev-parse", "HEAD"),
                "changed_path_count": len(git("status", "--porcelain").splitlines())}
    except (OSError, subprocess.TimeoutExpired):
        return {"is_git_checkout": True, "error": "git command unavailable"}


def network_probe() -> dict:
    # Only fixed, public domains are tested. IPs, headers and responses are not saved.
    results = {
        name: run_status(["getent", "ahostsv4", host])
        for name, host in (
            ("github_dns", "github.com"),
            ("pypi_dns", "pypi.org"),
            ("docker_registry_dns", "registry-1.docker.io"),
        )
    }
    if shutil.which("curl"):
        for name, url in (
            ("github_https", "https://github.com/"),
            ("pypi_https", "https://pypi.org/simple/"),
            ("docker_registry_https", "https://registry-1.docker.io/v2/"),
        ):
            # Curl 0 means HTTPS transport completed, NOT search API success.
            # An HTTP 401 from registry-1.docker.io is normal.
            results[name] = run_status(
                ["curl", "-sS", "-L", "-I", "--max-time", "8",
                 "-o", os.devnull, url], timeout=10,
            )
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Local diagnostic report; never reads API keys")
    ap.add_argument("--network", action="store_true", help="Check public DNS/HTTPS connectivity")
    args = ap.parse_args()

    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None

    mem_mib = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                mem_mib = round(int(line.split()[1]) / 1024)
                break
    except OSError:
        pass

    programs = {
        "git": run_status(["git", "--version"], show_version=True),
        "docker": run_status(["docker", "--version"], show_version=True),
        "docker_compose": run_status(["docker", "compose", "version"], show_version=True),
        "docker_daemon": run_status(["docker", "info", "--format", "{{.ServerVersion}}"], show_version=True),
        "curl": run_status(["curl", "--version"], show_version=True),
    }

    report = {
        "kind": "local_demo_preflight",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "virtualenv_active": sys.prefix != sys.base_prefix,
        "cpu_count": os.cpu_count(),
        "memory_total_mib": mem_mib,
        "workspace_disk_free_gib": round(shutil.disk_usage(ROOT).free / (1024**3), 2),
        "programs": programs,
        "package_versions": versions,
        "upstream_shas": upstream_shas(),
        "git": git_snapshot(),
        "ports": local_ports(),
        "proxy_variable_present": {
            name: bool(os.getenv(name) or os.getenv(name.lower()))
            for name in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")
        },
        "network": network_probe() if args.network else "NOT_RUN; add --network",
        "privacy": "Only allowlisted metadata collected; inspect JSON before sharing.",
    }
    output = ROOT / "reports" / "local" / "preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved: reports/local/preflight.json (review before sharing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
