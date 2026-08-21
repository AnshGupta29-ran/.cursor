"""Load seed dimensions for a category/index (language, UI, etc.)."""

from __future__ import annotations

import json
from pathlib import Path

from datagen_pipeline.paths import BANK


def load_seed_meta(category: str, index: int) -> dict:
    cat_dir = BANK / category
    matches = sorted(cat_dir.glob(f"{index:02d}_*.json"))
    if not matches:
        return {}
    try:
        return json.loads(matches[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def dimensions_for(category: str, index: int) -> dict:
    seed = load_seed_meta(category, index)
    hint = dict(seed.get("dimensions_hint") or {})
    hint.setdefault("language_runtime", "python")
    hint.setdefault("complexity", "medium")
    hint.setdefault("ui_surface", "static_html")
    hint.setdefault("persistence", "sqlite")
    return hint
