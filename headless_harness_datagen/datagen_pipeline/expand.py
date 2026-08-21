"""Expand each forged base task into many variant PRDs (path to ~5000 repos).

Rotates language_runtime / UI / persona / novelty so traces stay diverse
(Java, Rust, Go, C#, C++, TS, Python, ...).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from datagen_pipeline.paths import EXPAND_DIR, ensure_pipeline_dirs
from datagen_pipeline.queue import BIG_RUN_CATEGORIES, SKIP_DONE_KEYS, iter_base_items

PERSONAS = (
    "solo_founder",
    "enterprise_buyer",
    "open_source_maintainer",
    "security_auditor",
    "student_hacker",
)
NOVELTY = (
    "offline_first",
    "accessibility_keyboard",
    "chaos_fault_injection",
    "audit_trail_export",
    "multi_tenant_isolation",
    "dark_ops_console",
    "csv_roundtrip",
    "idempotent_retries",
    "feature_flag_gates",
)
LANGUAGES = (
    "python",
    "typescript",
    "javascript",
    "go",
    "rust",
    "java",
    "csharp",
    "cpp",
)
UI_FLIP = (
    "static_html",
    "react_spa",
    "cli_tui",
    "api_only",
    "desktop_window",
    "mobile_web",
    "html_canvas",
    "dashboard_charts",
)
PERSISTENCE = (
    "sqlite",
    "json_file",
    "csv_files",
    "localstorage",
    "memory_only",
)
COMPLEXITY_FLIP = {
    "low": ("medium", "hard"),
    "medium": ("low", "hard"),
    "hard": ("medium", "low"),
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def build_variant_prompt(base_text: str, *, variant_id: str, mutations: dict[str, str]) -> str:
    lines = [
        f"# VARIANT {variant_id} - synthetic expansion of the base PRD below",
        "",
        "## Dimension mutations (MANDATORY - override base locks if they conflict)",
    ]
    for k, v in mutations.items():
        lines.append(f"- **{k}**: `{v}`")
    lines += [
        "",
        "## Language lock",
        f"- Implement primarily in `{mutations['language_runtime']}`.",
        "- Do not homogenize to Python unless language_runtime is python.",
        "",
        "## Subtask acceptance extras",
        f"- Ship a distinct product codename suffix `-{variant_id}`.",
        "- Keep the same core job-to-be-done as the base PRD.",
        "- Add one stress scenario from the mutations.",
        "- README: run command, seed data, mutations applied.",
        "- Full working demo required (not a stub).",
        "- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.",
        "- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).",
        "- Outer VALIDATE gate rejects stubs before mark-done.",
        f"- Print `DONE <parent>__{variant_id}` when demoable.",
        "",
        "---",
        "",
        "## BASE PRD (honor unless mutated above)",
        "",
        base_text.strip(),
        "",
    ]
    return "\n".join(lines)


def expand_item(
    *,
    category: str,
    index: int,
    title: str,
    seed_id: str,
    platform_prompt: Path,
    workdir: str,
    complexity: str,
    base_language: str,
    variants_per_task: int,
    skip_existing: bool = False,
) -> list[Path]:
    ensure_pipeline_dirs()
    base = platform_prompt.read_text(encoding="utf-8")
    out_paths: list[Path] = []
    n = 0
    while n < variants_per_task:
        persona = PERSONAS[n % len(PERSONAS)]
        novelty = NOVELTY[n % len(NOVELTY)]
        # Force language diversity: cycle languages, avoid repeating base every time
        lang = LANGUAGES[(n + LANGUAGES.index(base_language) if base_language in LANGUAGES else n) % len(LANGUAGES)]
        if n % 3 == 0 and base_language in LANGUAGES:
            lang = base_language  # keep some variants on original stack
        ui = UI_FLIP[n % len(UI_FLIP)]
        persist = PERSISTENCE[n % len(PERSISTENCE)]
        cx_opts = COMPLEXITY_FLIP.get(complexity, ("medium",))
        cx = cx_opts[n % len(cx_opts)]
        variant_id = f"v{n+1:02d}_{_slug(lang)}_{_slug(persona)}_{_slug(novelty)}"
        mutations = {
            "language_runtime": lang,
            "user_persona": persona,
            "novelty_hook": novelty,
            "ui_surface": ui,
            "persistence": persist,
            "complexity": cx,
            "session_shape": "multi_turn_repair",
            "delivery": "cli_entry_plus_ui",
        }
        parent_key = f"{category}:{index:02d}"
        task_key = f"{parent_key}__{variant_id}"
        dest = EXPAND_DIR / category / f"{index:02d}_{variant_id}"
        prompt_path = dest / "platform_prompt.md"
        meta_path = dest / "variant_meta.json"
        if skip_existing and prompt_path.is_file() and meta_path.is_file():
            out_paths.append(prompt_path)
            n += 1
            continue
        dest.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(
            build_variant_prompt(base, variant_id=variant_id, mutations=mutations),
            encoding="utf-8",
        )
        meta = {
            "task_key": task_key,
            "parent_key": parent_key,
            "category": category,
            "index": index,
            "title": f"{title} [{variant_id}]",
            "seed_id": seed_id,
            "workdir": f"{workdir}__{variant_id}",
            "complexity": cx,
            "language_runtime": lang,
            "ui_surface": ui,
            "persistence": persist,
            "variant": variant_id,
            "mutations": mutations,
            "base_platform_prompt": str(platform_prompt),
        }
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        out_paths.append(prompt_path)
        n += 1
    return out_paths


def expand_categories(
    categories: list[str],
    *,
    variants_per_task: int,
    quiet: bool = False,
    skip_existing: bool = False,
) -> int:
    total = 0
    for item in iter_base_items(categories):
        if item.task_key in SKIP_DONE_KEYS:
            continue
        paths = expand_item(
            category=item.category,
            index=item.index,
            title=item.title,
            seed_id=item.seed_id,
            platform_prompt=Path(item.platform_prompt),
            workdir=item.workdir,
            complexity=item.complexity,
            base_language=item.language_runtime,
            variants_per_task=variants_per_task,
            skip_existing=skip_existing,
        )
        total += len(paths)
        if not quiet:
            print(f"  {item.task_key} ({item.language_runtime}): +{len(paths)} variants", flush=True)
    return total


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Expand forged tasks into variant PRDs")
    p.add_argument(
        "--categories",
        default=",".join(BIG_RUN_CATEGORIES),
        help="Comma-separated categories",
    )
    p.add_argument(
        "--variants-per-task",
        type=int,
        default=45,
        help="Variants per base task",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    print(
        f"Expand categories={len(cats)} variants_per_task={args.variants_per_task}",
        flush=True,
    )
    if args.dry_run:
        return 0
    n = expand_categories(cats, variants_per_task=args.variants_per_task)
    print(f"Wrote {n} variant PRDs under {EXPAND_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
