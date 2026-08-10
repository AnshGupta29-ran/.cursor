#!/usr/bin/env python3
"""CLI for the prompt-forge mid-layer.

Examples
--------
  python -m prompt_forge list
  python -m prompt_forge classify "Build a smart home dashboard with schedules"
  python -m prompt_forge forge "Collaborative whiteboard for architecture studios" --out artifacts/forge_demo
  python -m prompt_forge forge "Mini cloud storage for clinics" --compose --repo-path C:/tmp/clinic_drive
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prompt_forge.categories import CATEGORIES, Category, all_category_ids
from prompt_forge.classifier import classify
from prompt_forge.composer import compose_harness_objective, save_forge_artifacts
from prompt_forge.generator import generate_platform_prompt
from prompt_forge.templates import list_templates, load_template


def _load_dotenv() -> None:
    """Load repo .env without importing the gRPC client stack."""
    import os
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _llm_from_env():
    from controller.llm import OpenAICompatibleClient

    _load_dotenv()
    return OpenAICompatibleClient.from_env()


def cmd_list(_args: argparse.Namespace) -> int:
    print("Categories & templates:\n")
    templates = set(list_templates())
    for cat in Category:
        info = CATEGORIES[cat]
        mark = "OK" if cat.value in templates else "MISSING TEMPLATE"
        print(f"  [{mark}] {cat.value}")
        print(f"       {info.title}")
        print(f"       {info.description}")
        print(f"       examples: {', '.join(info.example_seeds)}")
        print()
    return 0


def cmd_show_template(args: argparse.Namespace) -> int:
    print(load_template(args.category))
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    llm = _llm_from_env() if args.llm else None
    result = classify(
        args.seed,
        category=args.category,
        llm=llm,
        use_llm=bool(args.llm),
    )
    print(
        json.dumps(
            {
                "category": result.category.value,
                "confidence": result.confidence,
                "method": result.method,
                "scores": result.scores,
            },
            indent=2,
        )
    )
    return 0


def cmd_forge(args: argparse.Namespace) -> int:
    llm = _llm_from_env()
    out = Path(args.out) if args.out else Path("artifacts") / "prompt_forge_last"
    out.mkdir(parents=True, exist_ok=True)

    if args.compose:
        result = compose_harness_objective(
            repo_path=args.repo_path,
            seed=args.seed,
            llm=llm,
            category=args.category,
            use_llm_classifier=args.llm_classify,
            diversity_hint=args.diversity_hint,
            temperature=args.temperature,
            include_verification=not args.skip_verification,
            max_repair_iterations=args.max_repair_iterations,
        )
        paths = save_forge_artifacts(result, out)
        print(f"Category: {result.category.value}")
        print(f"Wrote: {paths['platform_prompt']}")
        print(f"Wrote: {paths['composed']}")
        print(f"Wrote: {paths['meta']}")
        return 0

    generated = generate_platform_prompt(
        args.seed,
        llm,
        category=args.category,
        use_llm_classifier=args.llm_classify,
        diversity_hint=args.diversity_hint,
        temperature=args.temperature,
    )
    (out / "platform_prompt.md").write_text(generated.platform_prompt, encoding="utf-8")
    (out / "forge_meta.json").write_text(
        json.dumps(generated.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Category: {generated.category.value}")
    print(f"Wrote: {out / 'platform_prompt.md'}")
    print(f"Wrote: {out / 'forge_meta.json'}")
    if args.print:
        print("\n----- PLATFORM PROMPT -----\n")
        print(generated.platform_prompt)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt_forge",
        description="Generate unique platform prompts between task seeds and the harness",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List categories and template status")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show-template", help="Print a category template")
    p_show.add_argument("category", choices=all_category_ids())
    p_show.set_defaults(func=cmd_show_template)

    p_cls = sub.add_parser("classify", help="Classify a task seed")
    p_cls.add_argument("seed", help="Task seed / brief")
    p_cls.add_argument("--category", choices=all_category_ids(), default=None)
    p_cls.add_argument("--llm", action="store_true", help="Use LLM classifier")
    p_cls.set_defaults(func=cmd_classify)

    p_forge = sub.add_parser("forge", help="Forge a unique platform prompt")
    p_forge.add_argument("seed", help="Task seed / brief")
    p_forge.add_argument("--category", choices=all_category_ids(), default=None)
    p_forge.add_argument("--out", default=None, help="Output directory")
    p_forge.add_argument("--temperature", type=float, default=1.0)
    p_forge.add_argument("--diversity-hint", default=None)
    p_forge.add_argument(
        "--llm-classify",
        action="store_true",
        help="Use LLM for category classification",
    )
    p_forge.add_argument(
        "--compose",
        action="store_true",
        help="Also wrap with harness bootstrap (build_unified_pipeline_objective)",
    )
    p_forge.add_argument(
        "--repo-path",
        default="/tmp/prompt_forge_repo",
        help="Repository path embedded in composed harness objective",
    )
    p_forge.add_argument("--skip-verification", action="store_true")
    p_forge.add_argument("--max-repair-iterations", type=int, default=15)
    p_forge.add_argument("--print", action="store_true", help="Print platform prompt")
    p_forge.set_defaults(func=cmd_forge)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
