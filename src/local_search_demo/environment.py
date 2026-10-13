"""Offline environment inventory with an explicit allowlist, never os.environ."""

from datetime import datetime, timezone
from importlib import import_module, metadata
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys

IMPORTS = {
    "httpx": ("httpx", "AsyncClient"),
    "httpx2": ("httpx2", "AsyncClient"),
    "trafilatura": ("trafilatura", "extract"),
    "readability-lxml": ("readability", "Document"),
    "selectolax": ("selectolax.lexbor", "LexborHTMLParser"),
    "openai": ("openai", "OpenAI"),
    "fastapi": ("fastapi", "FastAPI"),
    "uvicorn": ("uvicorn", "run"),
    "pydantic": ("pydantic", "BaseModel"),
    "pytest": ("pytest", "main"),
}


def check_imports() -> list[dict]:
    checks = []
    for distribution, (module_name, symbol) in IMPORTS.items():
        try:
            module = import_module(module_name)
            getattr(module, symbol)
            checks.append({"package": distribution, "version": metadata.version(distribution),
                           "module": module_name, "symbol": symbol, "status": "PASS"})
        except (ImportError, AttributeError, metadata.PackageNotFoundError) as exc:
            checks.append({"package": distribution, "status": "FAIL", "error": str(exc)})
    return checks


def _git(directory: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(directory), *args],
                                       text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def environment_report(project_root: Path | None = None) -> dict:
    checks = check_imports()
    report = {
        "batch": "B00", "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "python": {"version": platform.python_version(), "implementation": platform.python_implementation(),
                   "executable": sys.executable},
        "platform": {"system": platform.system(), "release": platform.release(),
                     "machine": platform.machine(), "libc": list(platform.libc_ver())},
        "imports": checks,
        "packages": dict(sorted((d.metadata["Name"], d.version) for d in metadata.distributions())),
        "network_tests": "NOT_RUN", "searxng_deployment": "NOT_RUN", "model_calls": "NOT_RUN",
    }
    if project_root is not None:
        root = project_root.resolve()
        report["project"] = {"root": str(root), "revision": _git(root, "rev-parse", "HEAD"),
                             "branch": _git(root, "branch", "--show-current")}
        report["dependency_locks"] = {
            name: {"sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}
            for name in ("uv.lock", "requirements.lock", ".python-version") if (root / name).is_file()
        }
        lock = root / "upstream-lock.json"
        if lock.is_file():
            report["upstream"] = []
            for row in json.loads(lock.read_text(encoding="utf-8")):
                actual_sha = _git(root / row["path"], "rev-parse", "HEAD")
                report["upstream"].append({**row, "actual_sha": actual_sha,
                                            "checkout_matches_lock": actual_sha == row["sha"]})
    return report
