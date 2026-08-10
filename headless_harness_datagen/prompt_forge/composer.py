"""Compose forged platform prompts onto the existing harness bootstrap."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from prompt_forge.categories import Category
from prompt_forge.generator import GeneratedPlatformPrompt, generate_platform_prompt


PLATFORM_ADDON_HEADER = """==================================================
PLATFORM ADD-ON (GENERATED — READ FIRST)
This block was produced by the prompt-forge mid-layer for THIS task only.
It specializes the product. Obey it when shaping the repository.
The sandbox / lifecycle rules below still apply and take precedence on
execution boundaries, environment isolation, and verification markers.

SPEED: ship a runnable MVP fast. Batch file writes, skip multi-GB downloads /
IDE installs, run only fast smoke tests, and stop once green.
==================================================
"""


@dataclass
class ForgeResult:
    generated: GeneratedPlatformPrompt
    composed_objective: str
    addon_only: str

    @property
    def category(self) -> Category:
        return self.generated.category

    @property
    def platform_prompt(self) -> str:
        return self.generated.platform_prompt


def wrap_platform_addon(platform_prompt: str) -> str:
    return f"{PLATFORM_ADDON_HEADER}\n{platform_prompt.strip()}\n"


def merge_objective_with_addon(*, seed_or_objective: str, platform_prompt: str) -> str:
    """Replace a thin seed with the forged PRD while keeping seed as origin note."""
    addon = wrap_platform_addon(platform_prompt)
    return (
        f"{addon}\n"
        f"--------------------------------------------------\n"
        f"ORIGIN SEED (for traceability; prefer PLATFORM ADD-ON details above)\n"
        f"{seed_or_objective.strip()}\n"
        f"--------------------------------------------------"
    )


def compose_harness_objective(
    *,
    repo_path: str,
    seed: str,
    llm,
    max_repair_iterations: int = 15,
    include_verification: bool = True,
    category: Category | str | None = None,
    use_llm_classifier: bool = False,
    diversity_hint: str | None = None,
    temperature: float = 1.0,
) -> ForgeResult:
    """
    End-to-end: forge unique platform prompt, then wrap with harness lifecycle.

    Returns ForgeResult whose `composed_objective` is ready for ConversationRunner.
    """
    from verification.prompts import build_unified_pipeline_objective

    generated = generate_platform_prompt(
        seed,
        llm,
        category=category,
        use_llm_classifier=use_llm_classifier,
        diversity_hint=diversity_hint,
        temperature=temperature,
    )
    merged = merge_objective_with_addon(
        seed_or_objective=seed,
        platform_prompt=generated.platform_prompt,
    )
    composed = build_unified_pipeline_objective(
        repo_path=repo_path,
        objective=merged,
        max_repair_iterations=max_repair_iterations,
        include_verification=include_verification,
    )
    return ForgeResult(
        generated=generated,
        composed_objective=composed,
        addon_only=wrap_platform_addon(generated.platform_prompt),
    )


def forge_platform_prompt(
    seed: str,
    llm,
    **kwargs,
) -> GeneratedPlatformPrompt:
    """Alias used by package exports / backends that only need the add-on."""
    return generate_platform_prompt(seed, llm, **kwargs)


def save_forge_artifacts(result: ForgeResult, out_dir: Path) -> dict[str, Path]:
    """Persist forged prompt materials next to a run for debugging / datasets."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "platform_prompt": out_dir / "platform_prompt.md",
        "addon": out_dir / "platform_addon.md",
        "meta": out_dir / "forge_meta.json",
        "composed": out_dir / "composed_objective.md",
    }
    paths["platform_prompt"].write_text(result.platform_prompt, encoding="utf-8")
    paths["addon"].write_text(result.addon_only, encoding="utf-8")
    paths["composed"].write_text(result.composed_objective, encoding="utf-8")
    meta = result.generated.to_dict()
    from datetime import datetime, timezone

    meta["created_at"] = datetime.now(timezone.utc).isoformat()
    paths["meta"].write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    try:
        from prompt_stats.hooks import record_forge_event

        run_id = None
        # logs/<run-id>/prompt_forge
        if out_dir.name == "prompt_forge" and out_dir.parent.name:
            run_id = out_dir.parent.name
        record_forge_event(
            seed=result.generated.seed,
            platform_prompt=result.platform_prompt,
            category=result.category.value,
            classification=result.generated.classification.__dict__
            if hasattr(result.generated.classification, "__dict__")
            else {
                "category": result.generated.classification.category.value,
                "confidence": result.generated.classification.confidence,
                "method": result.generated.classification.method,
                "scores": result.generated.classification.scores,
            },
            template_used=result.generated.template_used,
            out_dir=out_dir,
            run_id=run_id,
            composed_objective=result.composed_objective,
        )
    except Exception:
        pass
    return paths
