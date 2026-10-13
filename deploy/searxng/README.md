# B01 local SearXNG

This is a self-hosted **meta-search** service. It relies on third-party upstream
engines; starting the container does not guarantee live results.

```bash
docker compose -f deploy/searxng/compose.yml up -d
docker compose -f deploy/searxng/compose.yml ps
curl -sS -G 'http://127.0.0.1:8080/search' \
  --data-urlencode 'q=python asyncio' --data-urlencode 'format=json'
```

`search.formats` explicitly enables JSON; without it SearXNG may return HTTP 403.
B01 CLI uses `SEARXNG_BASE_URL`, default `http://127.0.0.1:8080`.

The official image is pinned to the observed digest in `compose.yml`:
`sha256:9b61996edcc679fb6665290f95fda15389a14eda6060e41a25c63ab2758f2436`.
The image revision matches the B00 SearXNG source checkout; details are in
`reports/B01/image.json`.

On this Linux host, upstream access requires the existing loopback proxy.
The first default deployment returned no results because container DNS failed;
both that failure and the successful retry are preserved. Use this optional override:

```bash
export SEARXNG_OUTGOING_PROXY=http://127.0.0.1:7890
docker compose -f deploy/searxng/compose.yml -f deploy/searxng/compose.proxy.yml up -d
```

The override uses host networking to reach the existing proxy and binds Granian
to `127.0.0.1:8080`. It adds no proxy container and does not forward model/GitHub keys.
Compose 2.40.3 was tested, including its `!reset` handling for the port mapping.
`FORCE_OWNERSHIP=false` preserves the host's read-only mounted settings file.

Capture current runtime evidence after running the live-smoke script:

```bash
uv run --locked python scripts/b01-deployment-evidence.py
```

Stop the proxy-mode deployment with the same two `-f` arguments and `down`.
