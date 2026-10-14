"""Explainable B04 text selection. This is a heuristic, NOT a quality guarantee.

Only uses observed parser outputs and documented structural hints. Decisions
include every parser, its status, score and a reason; no hard-coded fixture anchors.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import re

from local_search_demo.schemas import ParserResult

ORDER = {"trafilatura": 0, "selectolax": 1, "readability": 2}


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def choose_result(parsers: list[ParserResult]) -> tuple[ParserResult | None, str, list[dict]]:
    readable = [
        p for p in parsers
        if p.status == "PASS" and p.text and p.text.strip()
    ]
    notes: list[dict] = []
    for p in parsers:
        if p not in readable:
            notes.append({
                "name": p.name, "status": p.status, "eligible": False,
                "score": None,
                "reason": "empty or failed: not a candidate",
            })
            continue
        score = {"trafilatura": 3, "selectolax": 2, "readability": 1}[p.name]
        reasons = [f"adapter baseline={score}"]
        selector = p.metadata.get("selected_selector")
        if p.name == "selectolax":
            if selector in ("article", "main", '[role="main"]', '[itemprop="articleBody"]'):
                score += 3
                reasons.append(f"semantic DOM container {selector}")
            elif selector == "body(fallback)":
                score -= 4
                reasons.append("body fallback (may contain navigation)")
        others = [other for other in readable if other is not p]
        canonical = _flat(p.text)
        agreements = sum(
            SequenceMatcher(None, canonical, _flat(other.text or ""), autojunk=False).ratio() >= 0.83
            for other in others
        )
        if agreements:
            score += min(agreements, 2)
            reasons.append(f"agreement with {agreements} other output(s)")
        if len(others) >= 2:
            lengths = sorted(len(_flat(other.text or "")) for other in others)
            typical = lengths[len(lengths) // 2]
            if typical > 80 and len(canonical) > typical * 1.22:
                score -= 4
                reasons.append("substantially longer than both alternatives: possible noise")
        notes.append({
            "name": p.name, "status": p.status, "eligible": True,
            "score": score, "chars": p.chars,
            "reason": "; ".join(reasons),
        })
    candidates = [n for n in notes if n["eligible"]]
    if not candidates:
        return None, "No parser returned readable text; no text was invented.", notes

    selected = max(candidates, key=lambda n: (n["score"], -ORDER[n["name"]]))
    winner = next(p for p in readable if p.name == selected["name"])
    rejected = ", ".join(
        f"{n['name']}({n['status']}; score={n['score']})"
        for n in notes if n["name"] != selected["name"]
    )
    reason = (
        f"Selected {winner.name} by explainable heuristic "
        f"(score={selected['score']}; {selected['reason']}). "
        f"Alternatives: {rejected or 'none'}. "
        "This selection is not a verified content-quality verdict."
    )
    return winner, reason, notes
