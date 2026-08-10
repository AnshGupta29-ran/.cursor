"""CLI for datagen dimensions, matrix planning, and spend stats."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from datagen_dims.costing import estimate_matrix_budget, pricing_from_env
from datagen_dims.matrix import plan_matrix, write_combination_catalog
from datagen_dims.stats import (
    category_token_averages,
    complexity_value_grid,
    spend_summary,
)
from datagen_dims.taxonomy import ALL_DIMENSIONS, taxonomy_export


ARTIFACTS = REPO / "artifacts" / "datagen_dims"


def cmd_list(_args: argparse.Namespace) -> int:
    tax = taxonomy_export()
    print("=== META dimensions ===")
    for d in ALL_DIMENSIONS:
        if d.layer != "meta":
            continue
        mark = "" if d.matrix_axis else " (optional axis)"
        print(f"  {d.id}{mark}: {', '.join(d.values)}")
    print("\n=== GENERIC (harness/ops) dimensions ===")
    for d in ALL_DIMENSIONS:
        if d.layer != "generic":
            continue
        mark = "" if d.matrix_axis else " (optional axis)"
        print(f"  {d.id}{mark}: {', '.join(d.values)}")
    print("\n=== QUALITY (every example) ===")
    for d in ALL_DIMENSIONS:
        if d.layer != "quality":
            continue
        print(f"  {d.id}: {', '.join(d.values)} — {d.description}")
    out = ARTIFACTS / "taxonomy.json"
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(tax, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    axes = None
    if args.axes:
        axes = [a.strip() for a in args.axes.split(",") if a.strip()]
    filters = {}
    if args.filter:
        # format: dim=v1|v2,dim2=v3
        for part in args.filter.split(","):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            filters[k.strip()] = {x.strip() for x in v.split("|") if x.strip()}
    plan = plan_matrix(
        include_optional=args.optional,
        full=args.full,
        starter=not args.all_core,
        filters=filters or None,
        axes_ids=axes,
        limit=args.sample,
    )
    print(f"Mode: {plan['mode']}")
    print(f"Axes: {[a['id'] for a in plan['axes']]}")
    print(f"Combinations: {plan['n_combinations']:,}")
    if plan.get("unfiltered_product") != plan["n_combinations"]:
        print(f"(unfiltered core product would be {plan['unfiltered_product']:,})")
    pricing = pricing_from_env()
    budget = estimate_matrix_budget(
        n_combinations=plan["n_combinations"],
        examples_per_combo=args.examples_per_combo,
        avg_input_tokens=args.avg_in,
        avg_output_tokens=args.avg_out,
        pricing=pricing,
    )
    print(
        f"If {args.examples_per_combo} examples/combo -> "
        f"{budget['n_examples']:,} examples"
    )
    print(
        f"Est. tokens: {budget['total_tokens']:,.0f}  "
        f"USD~${budget['usd']:,.2f}  compute_units~{budget['compute_units']:,.2f}"
    )
    print(
        f"(rates: in ${pricing.input_usd_per_m}/M  out ${pricing.output_usd_per_m}/M  "
        f"model={pricing.model})"
    )
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "matrix_plan.json").write_text(
        json.dumps({"plan": plan, "budget": budget}, indent=2), encoding="utf-8"
    )
    if args.write_catalog:
        path, n = write_combination_catalog(
            ARTIFACTS / "combinations.jsonl",
            include_optional=args.optional,
            full=args.full,
            starter=not args.all_core,
            filters=filters or None,
            axes_ids=axes,
            examples_per_combo=args.examples_per_combo,
        )
        print(f"Wrote {n:,} rows -> {path}")
    print("\nSample combinations:")
    for row in plan["sample"][: args.sample]:
        print(" ", row)
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    spend = spend_summary()
    print("=== Ledger spend (all recorded sessions/prompts) ===")
    print(
        f"records={spend['n_records']}  tokens={spend['total_tokens']:,.0f}  "
        f"USD~${spend['usd']:,.4f}  CU~{spend['compute_units']:,.4f}"
    )
    av = category_token_averages(group_by=args.group_by)
    print(f"\n=== Avg tokens / $ by {args.group_by} ===")
    for k, g in av["groups"].items():
        print(
            f"  {k:28} n={g['n_sessions']:3}  "
            f"avg_tok={g['avg_total_tokens']:8.0f}  "
            f"avg$={g['avg_usd']:.4f}  sum$={g['sum_usd']:.4f}"
        )
    grid = complexity_value_grid()
    print("\n=== complexity × value ===")
    for k, cell in sorted(grid["grid"].items()):
        print(
            f"  {k:16} n={cell['n']:3}  avg_tok={cell['avg_total_tokens']:.0f}  "
            f"avg$={cell['avg_usd']:.4f}"
        )
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "ledger_stats.json").write_text(
        json.dumps({"spend": spend, "by_group": av, "grid": grid}, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {ARTIFACTS / 'ledger_stats.json'}")
    return 0


def cmd_seeds(_args: argparse.Namespace) -> int:
    print(
        """
Seed / prompt locations (run with Chakra kimi3)
===============================================

1) docs/archive/project_prompts.md
   - ~27 numbered prompts + bonus bullets + 2 long PRDs
   - Best hand-authored bank

2) prompt.txt  (repo root)
   - Single full-stack habit-tracker PRD

3) prompt_forge/categories.py  example_seeds  (26 short seeds)
   - Expand with: python -m prompt_forge forge "SEED" --out artifacts/...

4) prompt_forge/templates/*.md  (13 category shapes)
   - Not runnable alone; used by forge

5) artifacts/forge_demo/platform_prompt.md
   artifacts/forge_image/platform_prompt.md
   - Already forged PRDs (paste into main.py or Chakra)

6) experiments/*/README.md  — generated projects (not seeds)

How to run (kimi3)
------------------
A. Start Chakra (once):
   cd harness/chakra
   # ensure .chakra-profile.json has OPENAI_MODEL=kimi3
   bun run dev:grpc     # or scripts/start_chakra.sh

B. One archive prompt via harness + forge:
   cd <repo root>
   python main.py "Create a real-time collaborative whiteboard..." --forge-prompt --workdir wb1

C. Raw prompt.txt:
   python main.py "$(Get-Content -Raw prompt.txt)" --workdir habit1

D. Interactive Chakra (paste platform_prompt.md):
   chakra   # in harness/chakra cwd
   # paste contents of artifacts/forge_demo/platform_prompt.md

E. Refresh stats (tokens / dimensions / $):
   python -m prompt_stats refresh
   python -m datagen_dims stats
   python -m prompt_stats serve
""".strip()
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="datagen_dims")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("list", help="List all dimensions")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("plan", help="Cross-product plan + cost estimate")
    s.add_argument("--optional", action="store_true", help="Include optional axes")
    s.add_argument(
        "--full",
        action="store_true",
        help="Use all matrix_axis dimensions (huge — pair with --filter)",
    )
    s.add_argument(
        "--all-core",
        action="store_true",
        help="Core axes without starter value filters (larger product)",
    )
    s.add_argument("--axes", default=None, help="Comma ids to use as axes")
    s.add_argument(
        "--filter",
        default=None,
        help="dim=a|b,other=c  restrict values",
    )
    s.add_argument("--sample", type=int, default=5, help="Sample rows to print")
    s.add_argument("--examples-per-combo", type=int, default=3)
    s.add_argument("--avg-in", type=float, default=25_000.0, help="Avg input tokens/example")
    s.add_argument("--avg-out", type=float, default=80_000.0, help="Avg output tokens/example")
    s.add_argument("--write-catalog", action="store_true")
    s.set_defaults(func=cmd_plan)

    s = sub.add_parser("stats", help="Per-category token/$ averages from ledger")
    s.add_argument(
        "--group-by",
        default="business_domain",
        help="Dimension id to group by",
    )
    s.set_defaults(func=cmd_stats)

    s = sub.add_parser("seeds", help="Where prompts live + how to run with kimi3")
    s.set_defaults(func=cmd_seeds)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
