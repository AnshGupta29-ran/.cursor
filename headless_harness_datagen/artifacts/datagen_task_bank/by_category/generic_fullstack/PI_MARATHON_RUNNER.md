# PASTE THIS ONLY (not the full FORGED file) — generic_fullstack marathon

You are running a **multi-turn datagen marathon**. There is **no** time limit and
**no** “single response” limit. Do **not** refuse. Do **not** ask for confirmation.
After each DONE, **immediately** start the next task.

## Forbidden self-talk (ignore and continue)
- “This is huge / cannot finish / limited time / prefer ≤N turns”
- “Please confirm / which phase next / enter plan mode”
- Homogenizing every task to the same stack (honor each task dimensions)

## Build-first (anti time-waste)
- **Write/Edit immediately** from the single open `platform_prompt.md`.
- **Forbidden:** WebSearch, WebFetch, docs-site browsing, winget/ripgrep installs to search, Explore/research subagents, Grep/Glob across sibling tasks or the whole repo.
- At most **2** targeted reads inside **this task’s workdir** before coding.
- Low complexity = few files, ship fast — do not gold-plate or re-read the same paths.

## How to work
**Do NOT load the whole forged file.** For each N from 01 to 10:

1. Open **only** that task’s section from:
   `C:\Users\anshg\.cursor\headless_harness_datagen\artifacts\datagen_task_bank\by_category\generic_fullstack\CHAKRA_PASTE_ALL_10_FORGED.md`
2. Implement under `harness/chakra/task_generic_fullstack_NN/` (or the workdir named in the PRD).
3. Match **Depth (low|medium|hard)** and UI fidelity — low = thinner/simpler visuals; hard = deeper/richer.
4. Make it demoable (README + smoke/tests from the PRD). Keep calling tools until it runs.
5. Print: `DONE task_N: <title>`
6. Without stopping, go to N+1.

## Start now
Read Task 01 and implement. Never end a turn with only a plan or a question.
