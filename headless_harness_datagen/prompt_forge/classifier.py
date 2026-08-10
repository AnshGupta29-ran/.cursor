"""Heuristic (+ optional LLM) category classification for task seeds."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Sequence

from prompt_forge.categories import CATEGORIES, Category


@dataclass(frozen=True)
class ClassificationResult:
    category: Category
    confidence: float
    method: str
    scores: dict[str, float]


def classify_heuristic(seed: str) -> ClassificationResult:
    """Score categories by keyword hits in the seed text."""
    text = seed.lower()
    scores: dict[str, float] = {}
    for cat, info in CATEGORIES.items():
        if cat == Category.GENERIC_FULLSTACK:
            continue
        hits = sum(1.0 for kw in info.keywords if kw in text)
        # Prefer longer/more specific keywords slightly
        weighted = 0.0
        for kw in info.keywords:
            if kw in text:
                weighted += 1.0 + min(len(kw), 24) / 24.0
        scores[cat.value] = hits + weighted

    if not scores or max(scores.values()) <= 0:
        return ClassificationResult(
            category=Category.GENERIC_FULLSTACK,
            confidence=0.35,
            method="heuristic_fallback",
            scores={Category.GENERIC_FULLSTACK.value: 0.35},
        )

    best_id = max(scores, key=scores.get)
    best = scores[best_id]
    second = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0.0
    # Softmax-ish confidence from margin
    confidence = min(0.95, 0.45 + (best - second) * 0.08 + best * 0.04)
    return ClassificationResult(
        category=Category(best_id),
        confidence=confidence,
        method="heuristic",
        scores=scores,
    )


_CLASSIFY_SYSTEM = """You classify software platform generation tasks into exactly one category id.
Return ONLY compact JSON: {"category":"<id>","confidence":0.0-1.0,"reason":"..."}.
Valid category ids:
{ids}
Prefer a specialized category over generic_fullstack when evidence exists.
"""


def classify_with_llm(seed: str, llm, *, temperature: float = 0.0) -> ClassificationResult:
    """Ask the controller LLM to pick a category; fall back to heuristic on failure."""
    heuristic = classify_heuristic(seed)
    ids = "\n".join(f"- {c.value}: {CATEGORIES[c].title}" for c in Category)
    messages = [
        {
            "role": "system",
            "content": _CLASSIFY_SYSTEM.format(ids=ids),
        },
        {
            "role": "user",
            "content": (
                f"Heuristic suggestion: {heuristic.category.value} "
                f"(confidence={heuristic.confidence:.2f}).\n\n"
                f"Task seed:\n{seed.strip()}"
            ),
        },
    ]
    try:
        raw = llm.complete(messages, temperature=temperature)
        data = _extract_json(raw)
        cat = Category(str(data["category"]).strip())
        conf = float(data.get("confidence", 0.7))
        return ClassificationResult(
            category=cat,
            confidence=max(0.0, min(1.0, conf)),
            method="llm",
            scores={**heuristic.scores, cat.value: conf},
        )
    except Exception:
        return heuristic


def classify(
    seed: str,
    *,
    category: Category | str | None = None,
    llm=None,
    use_llm: bool = False,
) -> ClassificationResult:
    """Resolve category: explicit override > optional LLM > heuristic."""
    from prompt_forge.categories import resolve_category

    forced = resolve_category(category)
    if forced is not None:
        return ClassificationResult(
            category=forced,
            confidence=1.0,
            method="explicit",
            scores={forced.value: 1.0},
        )
    if use_llm and llm is not None:
        return classify_with_llm(seed, llm)
    return classify_heuristic(seed)


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))
