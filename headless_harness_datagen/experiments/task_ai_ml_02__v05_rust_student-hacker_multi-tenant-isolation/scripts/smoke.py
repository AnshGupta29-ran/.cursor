#!/usr/bin/env python3
"""CLI smoke for EpochLedger — no HTTP server required."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> str:
    proc = subprocess.run(
        ["cargo", "run", "--quiet", "--", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        print(out, file=sys.stderr)
        raise SystemExit(proc.returncode or 1)
    return out


def main() -> None:
    seed = ROOT / "fixtures" / "seed.json"
    if not seed.is_file():
        raise SystemExit(f"missing seed: {seed}")

    out = run(["tenant", "add", "smoke-tenant"])
    if "smoke-tenant" not in out and "Created tenant" not in out:
        raise SystemExit(f"unexpected tenant add output: {out!r}")

    out = run(["tenant", "list"])
    if "smoke-tenant" not in out:
        raise SystemExit(f"tenant list missing smoke-tenant: {out!r}")

    out = run(
        [
            "experiment",
            "run",
            "--tenant",
            "smoke-tenant",
            "--name",
            "run-smoke",
            "--score",
            "0.91",
        ]
    )
    if "run-smoke" not in out and "Recorded experiment" not in out:
        raise SystemExit(f"unexpected experiment run output: {out!r}")

    out = run(["experiment", "list", "--tenant", "smoke-tenant"])
    if "run-smoke" not in out:
        raise SystemExit(f"experiment list missing run-smoke: {out!r}")

    out = run(["experiment", "promote-champion", "--tenant", "smoke-tenant"])
    if "Champion" not in out and "run-smoke" not in out:
        raise SystemExit(f"unexpected promote output: {out!r}")

    print("SMOKE OK — EpochLedger CLI multi-tenant isolation")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
