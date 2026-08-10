"""CLI for the autonomous harness debugger."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from debugger.analyze import analyze_run
from debugger.load import load_run, resolve_pipeline_dir
from debugger.metrics import compare_metrics, extract_metrics
from debugger.report import write_compare, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="debugger",
        description="Offline analysis of headless harness pipeline artifacts",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="Analyze a single run")
    analyze_p.add_argument(
        "run_path",
        type=Path,
        help="Path to logs/<run_id> or logs/<run_id>/pipeline",
    )
    analyze_p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Override output directory (default: <pipeline>/debug)",
    )
    analyze_p.add_argument(
        "--stall-cycles",
        type=int,
        default=5,
        help="Controller resume cycles without progress before flagging a stall (default: 5)",
    )

    compare_p = sub.add_parser("compare", help="Compare metrics of two runs")
    compare_p.add_argument("run_a", type=Path)
    compare_p.add_argument("run_b", type=Path)
    compare_p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write compare.json (default: stdout only; if set, also writes JSON)",
    )

    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _cmd_analyze(args.run_path, args.out, stall_cycles=args.stall_cycles)
    if args.command == "compare":
        return _cmd_compare(args.run_a, args.run_b, args.out)
    return 1


def _cmd_analyze(
    run_path: Path, out: Path | None, *, stall_cycles: int = 5
) -> int:
    run = load_run(run_path)
    analysis = analyze_run(run, stall_cycles=stall_cycles)
    debug_dir = write_report(analysis, out_dir=out)
    print(f"Wrote {debug_dir / 'report.md'}")
    print(f"Wrote {debug_dir / 'report.json'}")
    if analysis.failure.primary:
        p = analysis.failure.primary
        print(f"Primary failure: {p.category}/{p.subcategory} — {p.message}")
        if analysis.failure.termination_outcome:
            print(f"Termination outcome: {analysis.failure.termination_outcome}")
    else:
        print(f"Status: {analysis.metrics.final_status}")
    return 0


def _cmd_compare(run_a: Path, run_b: Path, out: Path | None) -> int:
    a = load_run(run_a)
    b = load_run(run_b)
    ma = extract_metrics(a)
    mb = extract_metrics(b)
    rows = compare_metrics(ma, mb)
    label_a = a.run_id or str(resolve_pipeline_dir(run_a))
    label_b = b.run_id or str(resolve_pipeline_dir(run_b))
    out_path = out
    if out_path is None:
        # Prefer writing under run_a pipeline/debug when convenient
        try:
            out_path = resolve_pipeline_dir(run_a) / "debug" / "compare.json"
        except Exception:
            out_path = None
    table = write_compare(rows, label_a=label_a, label_b=label_b, out_path=out_path)
    print(table)
    if out_path:
        print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
