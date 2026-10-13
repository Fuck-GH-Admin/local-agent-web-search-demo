"""Shared contract for offline tests, CLI, WebUI and future Agent tools.

B00 freezes core field names; later batches can extend models with a documented
schema migration, without silently changing meanings.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Status(str, Enum):
    NOT_RUN = "not_run"
    OK = "ok"
    EMPTY = "empty"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_IMPLEMENTED = "not_implemented"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchResult(StrictModel):
    title: str
    url: str
    snippet: str = ""
    engines: list[str] = Field(default_factory=list)
    rank: int | None = Field(default=None, ge=1)


class SearchPayload(StrictModel):
    status: Status = Status.NOT_RUN
    items: list[SearchResult] = Field(default_factory=list)
    elapsed_ms: float | None = Field(default=None, ge=0)
    errors: list[str] = Field(default_factory=list)


class FetchResult(StrictModel):
    status: Status = Status.NOT_RUN
    url_requested: str | None = None
    url_final: str | None = None
    http_status: int | None = Field(default=None, ge=100, le=599)
    content_type: str | None = None
    byte_count: int | None = Field(default=None, ge=0)
    elapsed_ms: float | None = Field(default=None, ge=0)
    error: str | None = None
    redirect_history: list[str] = Field(default_factory=list)


class ParserResult(StrictModel):
    name: Literal["trafilatura", "readability", "selectolax"]
    status: Status = Status.NOT_RUN
    title: str | None = None
    raw_output: str | None = None
    text: str | None = None
    char_count: int = Field(default=0, ge=0)
    elapsed_ms: float | None = Field(default=None, ge=0)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_text_length(self) -> "ParserResult":
        if self.text is not None and self.char_count != len(self.text):
            raise ValueError("char_count must equal len(text)")
        return self


class ReadResult(StrictModel):
    fetch: FetchResult = Field(default_factory=FetchResult)
    parsers: list[ParserResult] = Field(default_factory=list)
    selected_parser: str | None = None
    selection_reason: str | None = None
    selected_text: str | None = None

    @model_validator(mode="after")
    def selected_must_exist(self) -> "ReadResult":
        if self.selected_parser and self.selected_parser not in [p.name for p in self.parsers]:
            raise ValueError("selected_parser must refer to an actual parser result")
        return self


class ToolCallTrace(StrictModel):
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    elapsed_ms: float | None = Field(default=None, ge=0)
    error: str | None = None


class AgentTrace(StrictModel):
    provider: str | None = None
    model: str | None = None
    api_mode: Literal["chat_completions", "responses"] | None = None
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    answer: str | None = None
    cited_urls: list[str] = Field(default_factory=list)


class ExperimentRecord(StrictModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: Literal["search", "read", "agent"]
    query: str | None = None
    url: str | None = None
    search: SearchPayload | None = None
    read: ReadResult | None = None
    agent: AgentTrace | None = None
    total_elapsed_ms: float | None = Field(default=None, ge=0)
