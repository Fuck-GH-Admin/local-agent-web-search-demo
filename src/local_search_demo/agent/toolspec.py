"""B06 model-independent tool function specs, independent from the UI."""
from __future__ import annotations

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the local SearXNG engine and return ranked URLs. Use only when outside evidence is needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Read a public webpage URL obtained from previous search results using the local HTML extraction Core.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "minLength": 1},
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
]
