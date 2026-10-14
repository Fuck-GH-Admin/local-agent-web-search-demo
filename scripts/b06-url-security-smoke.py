#!/usr/bin/env python3
"""Repeatable guard evidence: controlled transports + a real loopback sentinel.

Default is offline and safe for CI. --live additionally reads public sites with
the production pinned transport, and exercises the live dispatcher using real
local SearXNG. Scripted calls do not constitute a real-model B07/G4 run.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

import httpx

from local_search_demo.agent.dispatcher import AgentToolDispatcher
from local_search_demo.fetch.public_network import PublicURLTransport, create_public_http_client
from local_search_demo.pipeline.reader import read_webpage

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = "93.184.215.14"
ARTICLE = (ROOT / "tests/fixtures/html/static_article.html").read_bytes()


async def probe(*, live: bool) -> dict:
    rows = []
    for name, addresses, redirect in [
        ("public_body", [PUBLIC], None),
        ("private_dns", ["127.0.0.1"], None),
        ("mixed_dns", [PUBLIC, "10.0.0.1"], None),
        ("ipv6_link_local_dns", ["fe80::1"], None),
        ("metadata_redirect", [PUBLIC], "http://169.254.169.254/latest/meta-data/"),
        ("alternate_numeric_redirect", [PUBLIC], "http://2130706433/"),
    ]:
        sent = []
        async def resolver(host, port):
            return addresses
        def reply(request):
            sent.append({"url": str(request.url), "host": request.headers["Host"], "sni": request.extensions["sni_hostname"]})
            if redirect:
                return httpx.Response(302, headers={"Location": redirect})
            return httpx.Response(200, content=ARTICLE, headers={"Content-Type": "text/html"})
        transport = PublicURLTransport(resolver=resolver, delegate=httpx.MockTransport(reply))
        async with create_public_http_client(transport=transport) as client:
            record = await read_webpage("https://article.example.org/a", client=client)
        expected = "PASS" if name == "public_body" else "URL_DENIED"
        observed = record.fetch.error.kind if record.fetch.error else record.fetch.status
        passed = observed == expected and len(sent) == (1 if name in ("public_body", "metadata_redirect", "alternate_numeric_redirect") else 0)
        rows.append({"name": name, "status": "PASS" if passed else "FAIL", "expected": expected,
                     "observed": observed, "sent_requests": sent, "audit": transport.audit})

    # A listening real service must receive zero requests. No monkeypatch/delegate
    # intercepts the default HTTP transport for these checks.
    hits = []
    class Sentinel(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200); self.end_headers(); self.wfile.write(b"private sentinel")
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Sentinel)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/sentinel"
        async def private_resolver(host, port):
            return ["127.0.0.1"]
        for name, target, transport in [
            ("real_loopback_literal", url, PublicURLTransport()),
            ("real_loopback_dns", "http://attack.example.org/sentinel", PublicURLTransport(resolver=private_resolver)),
        ]:
            async with create_public_http_client(transport=transport) as client:
                record = await read_webpage(target, client=client)
            observed = record.fetch.error.kind if record.fetch.error else record.fetch.status
            rows.append({"name": name, "status": "PASS" if observed == "URL_DENIED" and not hits else "FAIL",
                         "observed": observed, "audit": transport.audit, "sentinel_requests": len(hits)})
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)

    if live:
        for url in ["https://www.python.org/doc/essays/blurb/", "https://www.gnu.org/philosophy/free-sw.zh-cn.html"]:
            transport = PublicURLTransport()
            async with create_public_http_client(transport=transport) as client:
                record = await read_webpage(url, client=client)
            rows.append({"name": "production_public_https", "url": url,
                         "status": "PASS" if record.fetch.status == "PASS" else "FAIL",
                         "fetch": record.fetch.model_dump(mode="json"), "selected_parser": record.selected_parser,
                         "audit": transport.audit})
        # Query the actual deployed search service. Pick one actual returned
        # official-doc URL; do not fabricate the dispatcher's provenance set.
        transport = PublicURLTransport()
        async with httpx.AsyncClient(trust_env=False) as search_client:
            dispatcher = AgentToolDispatcher(client=search_client, mode="live", public_transport=transport)
            search = await dispatcher.execute("search_web", {"query": "python asyncio", "limit": 10})
            candidates = [x["url"] for x in search.get("items", [])
                          if httpx.URL(x["url"]).host in ("docs.python.org", "www.python.org")]
            outcome = await dispatcher.execute("read_webpage", {"url": candidates[0]}) if candidates else None
            rows.append({"name": "live_dispatcher_real_search_then_public_read",
                         "status": "PASS" if outcome and outcome["status"] == "PASS" else "FAIL",
                         "search_status": search["status"], "search_result_urls": [x["url"] for x in search.get("items", [])],
                         "selected_url": candidates[0] if candidates else None,
                         "read": {k: v for k, v in (outcome or {}).items() if k != "selected_text"},
                         "selected_text_chars": len((outcome or {}).get("selected_text", "")), "audit": transport.audit})
    return {"validation_id": "B06-URL-SEC-01", "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
            "mode": "offline_and_actual_public_network" if live else "offline_plus_real_loopback_sentinel",
            "real_model_G4": "NOT_RUN", "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/B06/url-security/smoke.json")
    args = parser.parse_args()
    result = asyncio.run(probe(live=args.live))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "checks": len(result["rows"]), "output": str(args.output)}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
