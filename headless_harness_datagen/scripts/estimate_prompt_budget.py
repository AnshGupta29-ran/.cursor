#!/usr/bin/env python3
"""Estimate how many tokens the datagen pipeline sends per Chakra turn.

Reads the latest trace.jsonl (or a path you pass) and prints a budget breakdown.
Actual upstream prompt_tokens appear in token_usage rows when the model responds.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _est_tokens(chars: int) -> int:
    return max(1, chars // 4)


def _load_trace(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def analyze_trace(path: Path) -> int:
    rows = _load_trace(path)
    if not rows:
        print(f"No trace rows in {path}")
        return 1

    print(f"Trace: {path}\n")

    bootstrap = ""
    for row in rows:
        if row.get("type") == "run_started":
            bootstrap = str(row.get("objective") or "")
            break

    if bootstrap:
        print("Bootstrap user message (first turn only):")
        print(f"  chars={len(bootstrap)}  est_tokens~{_est_tokens(len(bootstrap))}")
        print("  (Full SANDBOX policy is NOT inlined — it lives in HARNESS_POLICY.md on disk.)")
        print()

    print("Chakra gRPC fixed overhead per turn (slim mode, measured at server startup):")
    print("  system prompt     ~280 chars  ~70 tokens")
    print("  4 tool schemas    ~2500 chars ~625 tokens (slim; full Bash alone was ~4000+ tokens)")
    print("  typical turn-1 total ~1500-2000 est tokens when history is empty")
    print()

    turns: list[dict] = []
    for row in rows:
        t = row.get("type")
        if t == "backend_turn_start":
            turns.append(
                {
                    "turn_id": row.get("turn_id"),
                    "msg": str(row.get("message") or ""),
                    "tools": 0,
                    "tool_output_chars": 0,
                    "prompt_tokens": None,
                    "completion_tokens": None,
                }
            )
        elif t == "tool_response" and turns:
            turns[-1]["tools"] += 1
            turns[-1]["tool_output_chars"] += len(str(row.get("output") or ""))
        elif t == "token_usage" and turns:
            turns[-1]["prompt_tokens"] = row.get("prompt_tokens") or row.get("input_tokens")
            turns[-1]["completion_tokens"] = row.get("completion_tokens") or row.get("output_tokens")
        elif t == "backend_turn_completed" and turns:
            usage = (row.get("detail") or {}).get("usage") or {}
            if usage:
                turns[-1]["prompt_tokens"] = usage.get("prompt_tokens")
                turns[-1]["completion_tokens"] = usage.get("completion_tokens")

    if not turns:
        print("No backend_turn_start rows found.")
        return 0

    print("Per-turn summary:")
    for i, turn in enumerate(turns, 1):
        msg_chars = len(turn["msg"])
        hist_note = "resume nudge" if msg_chars < 500 else "bootstrap/full objective"
        line = (
            f"  turn {i}: user_msg={msg_chars}c (~{_est_tokens(msg_chars)} tok) "
            f"tools={turn['tools']} tool_output={turn['tool_output_chars']}c "
            f"({hist_note})"
        )
        if turn["prompt_tokens"]:
            line += f"  ACTUAL prompt_tokens={turn['prompt_tokens']} completion={turn['completion_tokens']}"
        else:
            bloated = turn["tool_output_chars"] > 8000
            if bloated:
                line += "  WARNING: large tool output in history -> next LLM call likely 10k+ tokens"
            elif turn["tools"] == 0:
                line += "  (0 tools — cold timeout if estPromptTokens~1500+ still hangs ~5min)"
        print(line)

    print(
        "\nProxy timeouts at 0 prompt_tokens mean the request never got a first token "
        "(usually payload too fat OR intermittent upstream). Check gRPC terminal for "
        "estPromptTokens~ and prompt_tokens= on success."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "trace",
        nargs="?",
        help="path to trace.jsonl (default: newest under logs/)",
    )
    args = parser.parse_args()
    if args.trace:
        path = Path(args.trace)
    else:
        candidates = sorted((ROOT / "logs").glob("*/pipeline/working/trace.jsonl"))
        if not candidates:
            print("No trace.jsonl under logs/ — pass a path explicitly.")
            return 1
        path = candidates[-1]
    if not path.is_file():
        print(f"Not found: {path}")
        return 1
    return analyze_trace(path)


if __name__ == "__main__":
    raise SystemExit(main())
