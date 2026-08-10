"""Entry point: python -m viper_trace [--seed N] [--mode manual|ai] [--difficulty NAME]"""
from __future__ import annotations

import argparse

from .config import DIFFICULTIES


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="viper_trace",
        description="Viper Trace — A* Snake Observatory",
    )
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed for deterministic food placement")
    parser.add_argument("--mode", choices=["manual", "ai"], default=None,
                        help="Skip the menu and start directly in this mode")
    parser.add_argument("--difficulty", choices=list(DIFFICULTIES), default=None,
                        help="Difficulty preset (used with --mode)")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    from .game import ViperTraceApp  # deferred: pygame import

    app = ViperTraceApp(seed=args.seed)
    if args.mode is not None:
        if args.difficulty:
            app.difficulty = DIFFICULTIES[args.difficulty]
        app.mode = args.mode
        app._start_run()
    app.run()


if __name__ == "__main__":
    main()
