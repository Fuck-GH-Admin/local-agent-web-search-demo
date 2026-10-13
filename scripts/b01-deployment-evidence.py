#!/usr/bin/env python3
"""Read-only snapshot of the running B01 instance; never saves container env."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import httpx

from local_search_demo.environment import environment_report

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/B01"
COMPOSE = ["docker", "compose", "-f", "deploy/searxng/compose.yml"]


def command(args):
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT, timeout=30)


def save(name, value):
    (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    container_id = command([*COMPOSE, "ps", "-q", "searxng"]).strip()
    if not container_id:
        raise SystemExit("B01 SearXNG container is not running")
    container = json.loads(command(["docker", "inspect", container_id]))[0]
    image = json.loads(command(["docker", "image", "inspect", container["Image"]]))[0]
    save("image.json", {
        "time_utc": timestamp, "image_reference": container["Config"]["Image"],
        "id": image["Id"], "repo_digests": image["RepoDigests"], "size_bytes": image["Size"],
        "labels": {key: value for key, value in image["Config"].get("Labels", {}).items()
                   if key in {"org.opencontainers.image.version", "org.opencontainers.image.revision",
                              "org.opencontainers.image.created", "org.opencontainers.image.source"}},
    })
    # Select only the bind setting; other container environment variables are excluded.
    bind = next((value.split("=", 1)[1] for value in container["Config"].get("Env", [])
                 if value.startswith("GRANIAN_HOST=")), None)
    save("compose-state.json", {
        "time_utc": timestamp, "container_id": container_id,
        "name": container["Name"], "image": container["Config"]["Image"],
        "state": {key: container["State"][key] for key in ["Status", "Running", "ExitCode", "StartedAt"]},
        "restart_count": container["RestartCount"],
        "network_mode": container["HostConfig"]["NetworkMode"],
        "port_bindings": container["HostConfig"]["PortBindings"], "granian_host": bind,
    })
    (OUTPUT / "compose-ps.txt").write_text(command([*COMPOSE, "ps"]), encoding="utf-8")
    (OUTPUT / "compose-logs.txt").write_text(command([*COMPOSE, "logs", "--no-color", "--tail=200"]), encoding="utf-8")
    with httpx.Client(trust_env=False, timeout=10) as client:
        health = client.get("http://127.0.0.1:8080/healthz")
        config = client.get("http://127.0.0.1:8080/config")
        health.raise_for_status()
        config.raise_for_status()
        settings = config.json()
    save("instance-config.json", {
        "time_utc": timestamp, "base_url": "http://127.0.0.1:8080",
        "health_http_status": health.status_code, "config_http_status": config.status_code,
        "version": settings["version"], "limiter": settings["limiter"]["enabled"],
        "public_instance": settings["public_instance"],
        "enabled_general_engines": [e["name"] for e in settings["engines"]
                                    if e["enabled"] and "general" in e["categories"]],
    })
    inventory = environment_report(ROOT)
    inventory["batch"] = "B01"
    inventory["searxng_deployment"] = "PASS"
    smoke = OUTPUT / "search-smoke.json"
    inventory["network_tests"] = (json.loads(smoke.read_text(encoding="utf-8"))["live_status"]
                                  if smoke.is_file() else "NOT_RUN")
    save("environment.json", inventory)
    files = ["deploy/searxng/compose.yml", "deploy/searxng/settings.yml"]
    if container["HostConfig"]["NetworkMode"] == "host":
        files.append("deploy/searxng/compose.proxy.yml")
    save("deployment.json", {
        "time_utc": timestamp, "compose_files": files,
        "config_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files},
        "docker_version": command(["docker", "version", "--format", "{{.Server.Version}} "]).strip(),
        "compose_version": command(["docker", "compose", "version", "--short"]).strip(),
        "uses_existing_host_proxy": container["HostConfig"]["NetworkMode"] == "host",
    })
    print("B01 deployment evidence saved; health HTTP 200, container running.")


if __name__ == "__main__":
    main()
