"""B07 local-only FastAPI entrance, sharing search/read/Agent Core with CLI.

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
from pydantic import BaseModel, ConfigDict, Field

from local_search_demo.fetch.httpx_fetcher import create_http_client
from local_search_demo.pipeline.reader import read_webpage
from local_search_demo.schemas import ExperimentRecord
from local_search_demo.search.searxng import search_web
from local_search_demo.agent.service import execute_agent, AgentConfigurationError
from local_search_demo.agent.provider import ModelProvider

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


class AgentInput(InputModel):
    question: str = Field(min_length=1, max_length=4000)
    tool_choice: str = "auto"
    allow_live_read: bool = False
    timeout: float = Field(default=70, gt=0, le=120)
    max_rounds: int = Field(default=6, ge=1, le=10)


def create_app(
    *,
    client_factory: Callable[[], httpx.AsyncClient] | None = None,
    searxng_base_url: str | None = None,
    agent_provider_factory: Callable[[], ModelProvider] | None = None,
    agent_live_read_opt_in: bool | None = None,
) -> FastAPI:
    """Dependency injection is used only for transport, never to duplicate Core."""
    factory = client_factory or create_http_client
    searxng_url = searxng_base_url or os.getenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
    read_opt_in = (os.getenv("LOCAL_AGENT_ALLOW_LIVE_READ") == "1"
                   if agent_live_read_opt_in is None else agent_live_read_opt_in)

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

    @app.post("/api/agent", response_model=ExperimentRecord)
    async def agent(payload: AgentInput, request: Request):
        # This is a loopback-only development UI. A malicious website must not
        # submit paid Agent jobs using a user's browser.
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
            return JSONResponse(status_code=403, content={
                "status": "FORBIDDEN", "message": "Cross-origin model execution denied",
            })
        if payload.tool_choice not in ("auto", "required", "none"):
            return JSONResponse(status_code=422, content={
                "status": "INVALID_ARGUMENTS", "message": "Unsupported tool choice",
            })
        if payload.allow_live_read and not read_opt_in:
            return JSONResponse(status_code=403, content={
                "status": "LIVE_READ_DISABLED",
                "message": "Set LOCAL_AGENT_ALLOW_LIVE_READ=1 and opt in on this request",
            })
        try:
            provider = agent_provider_factory() if agent_provider_factory else None
            return await execute_agent(
                payload.question, search_client=request.app.state.http_client,
                searxng_base_url=searxng_url, provider=provider,
                tool_choice=payload.tool_choice,
                allow_live_read=payload.allow_live_read,
                timeout=payload.timeout, max_rounds=payload.max_rounds,
                thinking="disabled",
            )
        except AgentConfigurationError as exc:
            return JSONResponse(status_code=503, content={
                "status": "BLOCKED", "message": str(exc),
            })

    return app


app = create_app()
