"""Complexity / size / structure metrics for a prompt body."""

from __future__ import annotations

import math
import re
from typing import Any


_WORD_RE = re.compile(r"[A-Za-z0-9_]+")
_HEADING_RE = re.compile(r"(?m)^#{1,6}\s+")
_CHECKBOX_RE = re.compile(r"(?m)^\s*- \[[ xX]\]\s+")
_BULLET_RE = re.compile(r"(?m)^\s*[-*]\s+")
_CODE_FENCE_RE = re.compile(r"```")


def analyze_prompt_text(text: str) -> dict[str, Any]:
    """Derive size + structural complexity signals from prompt text."""
    text = text or ""
    chars = len(text)
    lines = text.splitlines()
    words = _WORD_RE.findall(text)
    word_count = len(words)
    # Rough token estimate (~4 chars / token for English-ish prompts)
    est_tokens = max(1, math.ceil(chars / 4)) if chars else 0
    headings = len(_HEADING_RE.findall(text))
    checkboxes = len(_CHECKBOX_RE.findall(text))
    bullets = len(_BULLET_RE.findall(text))
    code_fences = len(_CODE_FENCE_RE.findall(text)) // 2
    unique_words = len({w.lower() for w in words})
    avg_line = (sum(len(L) for L in lines) / len(lines)) if lines else 0.0

    # Weighted complexity score (0–100 scale, soft-capped)
    raw = (
        min(chars / 200.0, 40)  # length
        + min(headings * 2.5, 20)
        + min(checkboxes * 1.5, 15)
        + min(bullets * 0.35, 15)
        + min(code_fences * 2.0, 5)
        + min(unique_words / 80.0, 5)
    )
    # Short but multi-feature build briefs (e.g. ecommerce + login + landing)
    low = text.lower()
    feature_hits = sum(
        1
        for kw in (
            "login",
            "auth",
            "ecommerce",
            "e-commerce",
            "inventory",
            "checkout",
            "payment",
            "dashboard",
            "api",
            "realtime",
            "real-time",
            "websocket",
            "database",
            "admin",
            "landing",
            "cart",
            "order",
        )
        if kw in low
    )
    raw += min(feature_hits * 3.5, 18)
    if re.search(r"\b(build|create|implement|generate)\b", low) and feature_hits >= 2:
        raw += 8
    complexity_score = round(min(100.0, raw), 1)
    return {
        "chars": chars,
        "lines": len(lines),
        "words": word_count,
        "unique_words": unique_words,
        "est_tokens": est_tokens,
        "headings": headings,
        "acceptance_checkboxes": checkboxes,
        "bullets": bullets,
        "code_fence_blocks": code_fences,
        "avg_line_chars": round(avg_line, 1),
        "complexity_score": complexity_score,
        "complexity_band": band_for_score(complexity_score),
        "complexity_source": "prompt_text",
    }


def band_for_score(score: float) -> str:
    if score < 20:
        return "low"
    if score < 45:
        return "medium"
    if score < 70:
        return "high"
    return "very_high"


def apply_effort_complexity(
    base: dict[str, Any],
    *,
    runtime_seconds: float | None = None,
    tool_calls: int = 0,
    output_chars: int = 0,
    assistant_messages: int = 0,
) -> dict[str, Any]:
    """Blend prompt-structure score with observed session effort.

    Wall-clock alone must not dominate: gpt-oss often idles between manual
    "continue" nudges, so a basic game can look 'very_high' after ~1h calendar
    time. Weight tool/output density more than hours.
    """
    out = dict(base)
    score = float(base.get("complexity_score") or 0)
    runtime_seconds = float(runtime_seconds or 0)
    hours = runtime_seconds / 3600.0
    tools = max(0, int(tool_calls or 0))
    msgs = max(0, int(assistant_messages or 0))
    out_chars = max(0, int(output_chars or 0))

    effort = 0.0
    # Soft wall-clock (was hours*35 → +45 @ ~1.3h — that mislabeled basic games)
    effort += min(15.0, hours * 10.0)
    effort += min(25.0, tools * 0.22)
    effort += min(12.0, out_chars / 10000.0)
    effort += min(8.0, msgs * 0.08)

    # Sparse tool activity + long calendar time = continue-loop inflation, not depth
    if hours >= 0.4 and tools < 40:
        effort = min(effort, 12.0)

    final = round(min(100.0, score + effort), 1)
    out["complexity_score_prompt_only"] = score
    out["complexity_effort_bonus"] = round(effort, 1)
    out["complexity_score"] = final
    out["complexity_band"] = band_for_score(final)
    out["complexity_source"] = "prompt_plus_effort"
    out["runtime_seconds"] = runtime_seconds or None
    out["tool_calls"] = tools
    out["output_chars"] = out_chars
    return out


def chars_to_tokens(chars: int) -> int:
    return max(0, math.ceil(max(0, chars) / 4))
