#!/usr/bin/env python3
"""B07 safe G4 pre-review: read ignored real trace JSON; emit no raw user/page text.

This reports whether machine-checkable requirements are satisfied, but NEVER
awards final G4 PASS. A human must inspect the local original and sign off.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def evaluate(full: dict) -> dict:
    trace = full.get("agent_trace") or {}
    calls = trace.get("tool_calls") or []
    search_events = [(i, t) for i, t in enumerate(calls)
                     if t.get("name") == "search_web" and t.get("status") == "PASS"]
    read_events = [(i, t) for i, t in enumerate(calls)
                   if t.get("name") == "read_webpage" and t.get("status") == "PASS"
                   and (t.get("result") or {}).get("selected_text")]
    ordered = any(i < j for i, _ in search_events for j, _ in read_events)
    citations = trace.get("cited_urls") or []
    verified_urls = {
        (t.get("result") or {}).get("url")
        for _, t in read_events
    }
    source_valid = bool(citations) and all(x in verified_urls for x in citations)
    checks = {
        "real_model_invoked": full.get("real_model_invoked") is True
                              and full.get("provider") == "openai-compatible",
        "autonomous_tool_choice": full.get("tool_choice") == "auto",
        "operator_enabled_safe_reads": full.get("live_read_enabled") is True,
        "complete_final_answer": trace.get("status") == "DONE"
                                 and bool(str(trace.get("answer") or "").strip()),
        "successful_search_then_read": ordered,
        "citation_matches_successful_read": source_valid,
        "no_unverified_url_citations": not trace.get("unverified_citations"),
    }
    return {
        "batch": "B07", "stage": "G4",
        "machine_checks": checks,
        "candidate": "READY_FOR_HUMAN_REVIEW" if all(checks.values())
                     else "NOT_READY",
        "human_signoff": "NOT_RUN",
        "tool_calls_total": len(calls),
        "search_calls_passed": len(search_events),
        "read_calls_with_text": len(read_events),
        "verified_citation_count": len(citations),
        "warning": "This metadata omits actual question, answer, source URLs and webpage text; human review of original local trace is still mandatory.",
    }


def render_markdown(review: dict) -> str:
    rows = ["# B07 G4 机器复核摘要（不是人工签收）", "",
            f"候选状态：**{review['candidate']}**；人工签收：**NOT_RUN**。", "",
            "| 校验 | 机器结果 |", "|---|---|"]
    rows.extend(
        f"| {name} | {'PASS' if ok else 'FAIL'} |"
        for name, ok in review["machine_checks"].items()
    )
    rows += [
        "", f"记录调用数：{review['tool_calls_total']}；成功搜索：{review['search_calls_passed']}；"
        f"成功读取正文：{review['read_calls_with_text']}；已核引用：{review['verified_citation_count']}。", "",
        "## 人工复核必须补做", "",
        "- [ ] 确认为实际模型 API 调用而非模拟；模型名、接口模式和执行时间已在私有日志核实。",
        "- [ ] 检查每条 tool_call_id、工具输入、执行结果及请求来源，确认没有伪造。",
        "- [ ] 逐段对照回答和网页正文，确认引用支持具体论断，不能只匹配 URL。",
        "- [ ] 对照 auto 控制题与联网题，记录自动选择工具表现；required 结果不算自主选择。",
        "- [ ] 检查错误、上下文注入、超时和敏感信息，并确认待补验索引。",
        "- [ ] 人工给出 PASS / FAIL / BLOCKED 结论、理由、时间和非敏感证据指针。",
        "", "此文件不包含原始回答与 URL，可按需脱敏后提交；不要推送 agent-live.json 原始日志。",
    ]
    return "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT/"reports/B07/agent-live.json")
    parser.add_argument("--output", type=Path, default=ROOT/"reports/B07/g4-local-review.md")
    args = parser.parse_args()
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        review = evaluate(raw)
    except (OSError, ValueError, TypeError) as exc:
        print("Cannot evaluate trace:", type(exc).__name__)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps({"candidate": review["candidate"],
                      "human_signoff": "NOT_RUN", "output": str(args.output)}))
    return 0 if review["candidate"] == "READY_FOR_HUMAN_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
