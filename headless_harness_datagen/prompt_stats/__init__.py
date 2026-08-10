"""Prompt statistics ledger for every Chakra prompt in this repo (past + future).

Folder layout
-------------
prompt_stats/                 # code package
artifacts/prompt_stats/       # durable data (tracked)
  ledger.jsonl                # append-only records
  dashboard.html              # generated overview
  latest.json                 # last refresh summary

Usage
-----
  python -m prompt_stats refresh     # backfill + rebuild dashboard
  python -m prompt_stats show        # print table
  python -m prompt_stats dashboard   # open HTML

Future prompts are auto-recorded when you:
  - run ``prompt_forge forge`` / ``main.py --forge-prompt``
  - finish a ``main.py`` pipeline run
"""

from __future__ import annotations

from prompt_stats.hooks import record_forge_event, record_pipeline_event, record_raw_prompt
from prompt_stats.ledger import LEDGER_PATH, STATS_DIR, iter_records, load_records
from prompt_stats.metrics import analyze_prompt_text

__all__ = [
    "LEDGER_PATH",
    "STATS_DIR",
    "analyze_prompt_text",
    "iter_records",
    "load_records",
    "record_forge_event",
    "record_pipeline_event",
    "record_raw_prompt",
]
