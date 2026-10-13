import json
import pytest
from pydantic import ValidationError

from local_search_demo.schemas import (
    ExperimentRecord, FetchResult, ParserResult, ReadResult, SearchPayload,
    SearchResult, Status, ToolCallTrace, AgentTrace,
)


def test_search_serialization_roundtrip():
    record = ExperimentRecord(mode="search", query="电磁干扰", search=SearchPayload(
        status=Status.OK, items=[SearchResult(title="文章", url="https://example.org/a", rank=1)]
    ))
    restored = ExperimentRecord.model_validate_json(record.model_dump_json())
    assert restored.search.items[0].title == "文章"
    assert json.loads(record.model_dump_json())["mode"] == "search"


def test_parser_char_count_contract():
    assert ParserResult(name="selectolax", status=Status.OK, text="中文", char_count=2).char_count == 2
    with pytest.raises(ValidationError):
        ParserResult(name="selectolax", status=Status.OK, text="中文", char_count=999)


def test_selection_requires_present_parser():
    with pytest.raises(ValidationError):
        ReadResult(selected_parser="trafilatura")
    valid = ReadResult(
        fetch=FetchResult(url_requested="https://example.org"),
        parsers=[ParserResult(name="trafilatura", text="text", char_count=4)],
        selected_parser="trafilatura",
    )
    assert valid.selected_parser == "trafilatura"


def test_trace_has_no_invented_tool_calls():
    trace = AgentTrace(tool_calls=[ToolCallTrace(tool_call_id="tc_1", tool_name="search_web", arguments={"query": "test"})])
    assert trace.tool_calls[0].result is None
