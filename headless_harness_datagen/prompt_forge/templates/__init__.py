"""Load durable category templates from disk."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from prompt_forge.categories import Category

TEMPLATES_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=32)
def load_template(category: Category | str) -> str:
    """Return the markdown template body for a category."""
    if isinstance(category, str):
        category = Category(category)
    path = TEMPLATES_DIR / f"{category.value}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Missing category template: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if len(text) < 400:
        raise ValueError(f"Template too short for category {category.value}: {path}")
    return text


def list_templates() -> list[str]:
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.md"))


def template_path(category: Category | str) -> Path:
    if isinstance(category, str):
        category = Category(category)
    return TEMPLATES_DIR / f"{category.value}.md"
