# Why pasting ALL_10_FORGED into Pi fails (and how to run 13×10)

## What the terminal showed

`gpt-oss-120b` received the full ~1000-line `CHAKRA_PASTE_ALL_10_FORGED.md` and reasoned:

> “This is huge… cannot complete all… limited time… implement only first task”

So it **self-imposed** a 1-task limit. Our “no time budget” lines in the forged file
do **not** override that model habit when the entire marathon is dumped into one prompt.

## Root causes (blocks 13 categories × 10 tasks)

1. **Paste shape** — dumping 10 full PRDs ≈ burns context and triggers “too big” refusal.
2. **Model** — `gpt-oss-120b` often ends a turn with prose/confirmation (no tools). That
   paints `Cooked/Churned for Xm` and waits for human `continue`. Fixed in-harness via
   `CLAUDE.md` + Stop auto-continue hook + `CLAUDE_CODE_MAX_OUTPUT_TOKENS=65536`
   under `harness/chakra/`.
3. **Other categories** — any remaining `Time budget (~8/15/25 min)` lines reinforce refusal.
4. **Playing games ≠ datagen** — only implement sessions write synthetic traces.

## Correct pattern (use this)

| Step | What to paste / run |
|------|---------------------|
| 1 | Thin runner only: `games/PI_MARATHON_RUNNER.md` (~40 lines) |
| 2 | Agent **reads one** `## Task 0N` section from FORGED file per task |
| 3 | Implement → `DONE task_N` → read next section (same session) |
| 4 | Stats: `python -m prompt_stats serve` → filter Agent → pi |

**Do not** paste the entire FORGED markdown into the chat.

For each of the 13 categories, use the same pattern: a short `PI_MARATHON_RUNNER.md`
that points at that category’s FORGED file + `task_<cat>_NN` workdirs.

## Optional stronger setups

- Stronger / longer-horizon model than `gpt-oss-120b` for marathons.
- Outer loop script: after each `DONE task_N`, send “continue with task N+1” automatically.
- One Pi session per task (still datagen; ledger aggregates by agent).
