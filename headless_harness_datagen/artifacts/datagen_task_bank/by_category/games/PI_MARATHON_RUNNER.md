# PASTE THIS ONLY (not the full FORGED file) — Pi games marathon

You are running a **multi-turn datagen marathon**. There is **no** time limit and
**no** “single response” limit. Do **not** refuse. Do **not** decide “only task 1”.
Do **not** invent a wall-clock budget. After each DONE, **immediately** start the next.

## Forbidden self-talk (if you think these, ignore them and continue)
- “This is huge / unrealistic / cannot finish all 10”
- “Limited time / only start with task 1”
- “Maybe just print DONE without implementing”
- “Collapse everything to pygame stubs”

## How to work (critical — saves context)
**Do NOT load the whole forged file into your head.** For each N from 01 to 10:

1. Open **only** that task’s section from:
   `C:\Users\anshg\.cursor\headless_harness_datagen\artifacts\datagen_task_bank\by_category\games\CHAKRA_PASTE_ALL_10_FORGED.md`
   (search for `## Task 0N` / `## Task N` — read that section through the next `## Task` or EOF).
2. Implement under `harness/chakra/task_games_NN/` honoring that task’s **dimensions**
   (language, UI, complexity depth, verification). Replace wrong stubs.
3. Make it demoable (README run command + smoke/test from the PRD).
4. Print: `DONE task_N: <title> — <path> — how to run`
5. **Without stopping**, go to step 1 for N+1.

## Already done? Skip only if real
If a workdir already fully matches the forged PRD and smoke passes, print
`DONE task_N: … (verified existing)` and continue. Generic pygame stubs that do
**not** match the PRD must be replaced.

## Start now
Read Task 01 section from the forged file and implement it. When DONE, continue 02→10
in this same session. Never stop after one task because of “limits”.
