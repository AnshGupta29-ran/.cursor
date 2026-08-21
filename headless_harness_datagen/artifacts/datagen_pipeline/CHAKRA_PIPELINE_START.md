# PASTE INTO CHAKRA (kimi3) — big pipeline run

Plan mode OFF. No questions. No plan-only.
Ignore red Stop-hook / AUTO-CONTINUE labels.

## Setup (operator already ran)
```
python -m datagen_pipeline next --base-only --model kimi3
```

## You do now
1. Open **ONLY** `CHAKRA_NEXT_TASK.md` in this folder (or `artifacts/datagen_pipeline/CHAKRA_NEXT_TASK.md`).
2. Open the single `platform_prompt.md` path it names.
3. Honor **language_runtime** (java/rust/go/csharp/cpp/ts/python/…). Do not homogenize to Python.
4. Build a **complete working product** (seeded data, happy path, README). Not a stub.
5. Pace: low = few files fast; do not burn hours on installs.
6. Print `DONE <task_key>: … - path + how to run` then **STOP**.

Do **NOT** open any `CHAKRA_PASTE_ALL_10*.md`.

Operator will run `mark-done` and feed the next thin prompt.
