"""Shared JSON contracts from execution-plan section 3.

Unexecuted stages stay null; empty lists never imply a successful stage.
Timing values are milliseconds. Raw HTML belongs in a separate referenced file.
"""

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ErrorDetail(Contract):
    kind: str
    message: str


class SearchItem(Contract):
    title: str | None = None
    url: str
    snippet: str | None = None
    engines: list[str] = Field(default_factory=list)
    rank: int | None = Field(default=None, ge=1)


class SearchResult(Contract):
    status: str | None = None
    items: list[SearchItem] = Field(default_factory=list)
    elapsed_ms: float | None = Field(default=None, ge=0)
    errors: list[ErrorDetail] = Field(default_factory=list)


class FetchResult(Contract):
    status: str | None = None
    url_requested: str | None = None
    url_final: str | None = None
    http_status: int | None = Field(default=None, ge=100, le=599)
    content_type: str | None = None
    bytes: int | None = Field(default=None, ge=0)
    encoding: str | None = None
    html_path: str | None = None
    elapsed_ms: float | None = Field(default=None, ge=0)
    error: ErrorDetail | None = None


class ParserResult(Contract):
    name: Literal["trafilatura", "readability", "selectolax"]
    status: str | None = None
    raw_output: str | None = None
    text: str | None = None
    title: str | None = None
    chars: int | None = Field(default=None, ge=0)
    elapsed_ms: float | None = Field(default=None, ge=0)
    error: ErrorDetail | None = None


class ReadResult(Contract):
    fetch: FetchResult | None = None
    parsers: list[ParserResult] = Field(default_factory=list)
    selected_parser: Literal["trafilatura", "readability", "selectolax"] | None = None
    selection_reason: str | None = None


class ToolCall(Contract):
    call_id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    status: str | None = None
    elapsed_ms: float | None = Field(default=None, ge=0)
    error: ErrorDetail | None = None


class AgentTrace(Contract):
    provider: str | None = None
    model: str | None = None
    api_mode: Literal["chat_completions", "responses"] | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    answer: str | None = None
    cited_urls: list[str] = Field(default_factory=list)


class ExperimentRecord(ReadResult):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: Literal["search", "read", "agent"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    query: str | None = None
    url: str | None = None
    search: SearchResult | None = None
    agent: AgentTrace | None = None
    total_elapsed_ms: float | None = Field(default=None, ge=0)
