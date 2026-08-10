"""Fast headless smoke run: fixed-seed AI game must score > 0 within N ticks.

Usage: python -m viper_trace.smoke [seed] [max_ticks]
Exit code 0 on success, 1 on failure.
"""
from __future__ import annotations

import sys

from .config import DIFFICULTIES
from .engine import GameEngine, MODE_AI


def run_smoke(seed: int = 42, max_ticks: int = 3000) -> bool:
    ok = True
    for name, difficulty in DIFFICULTIES.items():
        eng = GameEngine(difficulty, MODE_AI, seed=seed)
        ticks = 0
        while ticks < max_ticks and eng.score == 0 and eng.alive and not eng.won:
            eng.tick()
            ticks += 1
        status = "OK" if eng.score > 0 else "FAIL"
        if eng.score == 0:
            ok = False
        print(
            f"[{status}] {difficulty.name}: score={eng.score} pellets={eng.pellets} "
            f"ticks={eng.ticks} alive={eng.alive}"
        )
    return ok


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    max_ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    sys.exit(0 if run_smoke(seed, max_ticks) else 1)
