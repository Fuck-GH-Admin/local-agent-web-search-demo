"""B05 local-only FastAPI entrance, sharing B01/B04 Core with the CLI.

Only the web transport and display are new. HTTPX client is reused via lifespan.
Do not publish the unauthenticated development app to a network interface.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Callable

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, ConfigDict

from local_search_demo.fetch.httpx_fetcher import create_http_client
from local_search_demo.pipeline.reader import read_webpage
from local_search_demo.schemas import ExperimentRecord
from local_search_demo.search.searxng import search_web

STATIC = Path(__file__).resolve().parent / "static"


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchInput(InputModel):
    query: str
    limit: int = 10
    language: str | None = None
    time_range: str | None = None
    timeout: float = 10.0


class ReadInput(InputModel):
    url: str
    timeout: float = 8.0
    max_bytes: int = 2 * 1024 * 1024


def create_app(
    *,
    client_factory: Callable[[], httpx.AsyncClient] | None = None,
    searxng_base_url: str | None = None,
) -> FastAPI:
    """Dependency injection is used only for transport, never to duplicate Core."""
    factory = client_factory or create_http_client
    searxng_url = searxng_base_url or os.getenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with factory() as client:
            app.state.http_client = client
            yield

    app = FastAPI(
        title="Local Agent Web Search Demo",
        description="B05: search and read share the same Python Core as the CLI",
        version="0.0.1",
        lifespan=lifespan,
    )

    # Prevent DNS-rebinding access through arbitrary host headers. B05 is local-only.
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["127.0.0.1", "localhost", "testserver"],
    )

    @app.middleware("http")
    async def local_safety_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/static/app.css", include_in_schema=False)
    async def stylesheet() -> FileResponse:
        return FileResponse(STATIC / "app.css", media_type="text/css")

    @app.get("/static/app.js", include_in_schema=False)
    async def javascript() -> FileResponse:
        return FileResponse(STATIC / "app.js", media_type="text/javascript")

    @app.get("/health")
    async def health() -> dict:
        # Readiness of the app only; does NOT probe SearXNG or upstream engines.
        return {"status": "ok", "app": "local-search-demo", "phase": "B05",
                "search_engine_checked": False}

    @app.post("/api/search", response_model=ExperimentRecord)
    async def search(payload: SearchInput, request: Request) -> ExperimentRecord:
        result = await search_web(
            payload.query,
            base_url=searxng_url,
            limit=payload.limit, language=payload.language,
            time_range=payload.time_range, timeout=payload.timeout,
            client=request.app.state.http_client,
        )
        return ExperimentRecord(
            mode="search", query=payload.query, search=result,
            total_elapsed_ms=result.elapsed_ms,
        )

    @app.post("/api/read", response_model=ExperimentRecord)
    async def read(payload: ReadInput, request: Request) -> ExperimentRecord:
        return await read_webpage(
            payload.url, client=request.app.state.http_client,
            timeout=payload.timeout, max_bytes=payload.max_bytes,
        )

    @app.post("/api/agent", status_code=501)
    async def agent_placeholder() -> JSONResponse:
        return JSONResponse(status_code=501, content={
            "status": "NOT_IMPLEMENTED", "phase": "B05",
            "message": "Agent tool calling is scheduled for B06/B07, not available yet.",
        })

    return app


app = create_app()
