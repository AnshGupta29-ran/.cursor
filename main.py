#!/usr/bin/env python3
"""Launcher — real game lives in the task_games_04 workdir.

Run:
  python main.py
  python main.py --smoke
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parent
    / "headless_harness_datagen"
    / "harness"
    / "chakra"
    / "task_games_04"
    / "main.py"
)

if not TARGET.is_file():
    sys.exit(f"Game not found: {TARGET}")

sys.argv[0] = str(TARGET)
runpy.run_path(str(TARGET), run_name="__main__")
