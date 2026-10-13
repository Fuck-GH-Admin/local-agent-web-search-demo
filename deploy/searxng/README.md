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

`image:latest` is deliberately a **floating proof-of-concept image**: record
the actual digest via `docker image inspect` during G1 and pin for subsequent
reproducibility; no digest is claimed before the local pull. Do not expose the
local demo settings publicly.
