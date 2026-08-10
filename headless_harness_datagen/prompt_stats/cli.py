"""CLI: python -m prompt_stats refresh|show|dashboard."""

from __future__ import annotations

import argparse
import json
import webbrowser
from pathlib import Path

from prompt_stats.collectors import refresh_all
from prompt_stats.ledger import DASHBOARD_PATH, LEDGER_PATH, LATEST_PATH, load_records
from prompt_stats.report import render_text_table, summarize, write_dashboard


def cmd_refresh(_args: argparse.Namespace) -> int:
    counts = refresh_all()
    path = write_dashboard()
    summary = summarize()
    print("Backfill counts:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"Ledger: {LEDGER_PATH} ({summary['total_records']} records)")
    print(f"Dashboard: {path}")
    print(f"Latest JSON: {LATEST_PATH}")
    return 0


def cmd_show(_args: argparse.Namespace) -> int:
    records = load_records()
    if not records:
        print("No records. Run: python -m prompt_stats refresh")
        return 1
    summary = summarize(records)
    print(
        f"records={summary['total_records']}  "
        f"avg_complexity={summary['avg_complexity_score']}  "
        f"avg_tokens~={summary['avg_est_tokens']}  "
        f"avg_runtime={summary['avg_runtime_seconds']}"
    )
    print()
    print(render_text_table(records))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    path = write_dashboard()
    print(path)
    if not args.no_open:
        webbrowser.open(path.resolve().as_uri())
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from prompt_stats.server import run_server

    if not args.no_open:
        threading = __import__("threading")
        threading.Timer(
            0.8,
            lambda: webbrowser.open(f"http://{args.host}:{args.port}/"),
        ).start()
    run_server(host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prompt_stats",
        description="Statistics for every Chakra prompt in this repo (past + future)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("refresh", help="Backfill from logs/forge/history + rebuild dashboard")
    s.set_defaults(func=cmd_refresh)

    s = sub.add_parser("show", help="Print ledger table")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("dashboard", help="Rebuild and open static HTML snapshot")
    s.add_argument("--no-open", action="store_true")
    s.set_defaults(func=cmd_dashboard)

    s = sub.add_parser(
        "serve",
        help="Interactive analytics UI with live Chakra history sync (graphs)",
    )
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8787)
    s.add_argument("--no-open", action="store_true")
    s.set_defaults(func=cmd_serve)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
