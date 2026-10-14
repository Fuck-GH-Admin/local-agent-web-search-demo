"""B08 evidence collector must not do live work unless explicitly requested."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/b08-validation.py"


def functions():
    return runpy.run_path(str(SCRIPT))


def test_b08_starts_with_six_distinct_grounded_real_sites():
    urls=functions()["source_urls"]()
    assert len(urls)>=5
    assert len({u.split("/")[2] for _,u in urls})>=5
    assert all(url.startswith("https://") for _,url in urls)


def test_b08_hash_is_payload_only_and_prior_evidence_referenced():
    fx=functions()
    assert fx["sha"]("sample")==hashlib.sha256(b"sample").hexdigest()
    assert set(fx["validate_prior_evidence"]())=={"G2","G3","B06_safety","G4"}


def test_b08_requires_explicit_optin_for_private_raw(tmp_path):
    result=subprocess.run(
        [sys.executable,str(SCRIPT),"--save-private",
         "--output",str(tmp_path/"never.json")],
        cwd=ROOT,capture_output=True,text=True,timeout=15,
    )
    assert result.returncode==2
    assert "requires --live" in result.stderr
    assert not (tmp_path/"never.json").exists()


def test_b08_help_works_without_running_network(tmp_path):
    result=subprocess.run(
        [sys.executable,str(SCRIPT),"--help"],
        cwd=ROOT,capture_output=True,text=True,timeout=15,
    )
    assert result.returncode==0
    assert "--live" in result.stdout
    assert not list(tmp_path.iterdir())
