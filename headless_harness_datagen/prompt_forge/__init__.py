"""Smart platform-prompt forge — sits between task seeds and the Chakra harness.

Flow
----
1. Take a short task brief / seed objective.
2. Classify it into a platform category (heuristic, optional LLM refine).
3. Load that category's durable template (shared shape for the family).
4. Ask an LLM to expand template + seed into a **unique** platform add-on prompt.
5. Compose the add-on onto the existing harness bootstrap (sandbox + lifecycle).

The original harness system / pipeline prompt is unchanged. The forged prompt is
an **add-on** the coding agent sees first for product uniqueness, then executes
the same plan → implement → verify lifecycle.
"""

from __future__ import annotations

from prompt_forge.categories import CATEGORIES, Category, resolve_category
from prompt_forge.composer import ForgeResult, compose_harness_objective, forge_platform_prompt
from prompt_forge.generator import GeneratedPlatformPrompt, generate_platform_prompt
from prompt_forge.templates import load_template, list_templates

__all__ = [
    "CATEGORIES",
    "Category",
    "ForgeResult",
    "GeneratedPlatformPrompt",
    "compose_harness_objective",
    "forge_platform_prompt",
    "generate_platform_prompt",
    "list_templates",
    "load_template",
    "resolve_category",
]
