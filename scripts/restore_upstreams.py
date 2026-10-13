#!/usr/bin/env python3
"""Restore the six public reference checkouts to the recorded commits."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(directory, *args):
    return subprocess.check_output(["git", "-C", str(directory), *args], text=True).strip()


def main():
    for row in json.loads((ROOT / "upstream-lock.json").read_text(encoding="utf-8")):
        path = ROOT / row["path"]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", row["url"], str(path)], check=True)
        if git(path, "status", "--porcelain"):
            raise SystemExit(f"Refusing to alter a modified upstream checkout: {row['name']}")
        if git(path, "rev-parse", "HEAD") != row["sha"]:
            subprocess.run(["git", "-C", str(path), "checkout", "--detach", row["sha"]], check=True)
        if row["recursive"]:
            subprocess.run(["git", "-C", str(path), "submodule", "update", "--init", "--recursive"], check=True)
            actual = git(path, "submodule", "status", "--recursive").splitlines()
            # Leading whitespace denotes initialized, matching submodule commits.
            if any(line.startswith(("-", "+", "U")) for line in actual):
                raise SystemExit(f"Unpinned submodule: {row['name']}")
        digest = hashlib.sha256((path / row["license_file"]).read_bytes()).hexdigest()
        if digest != row["license_sha256"]:
            raise SystemExit(f"License checksum differs: {row['name']}")
        print(f"{row['name']}: PASS {row['sha']}")


if __name__ == "__main__":
    main()
