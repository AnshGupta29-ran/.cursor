# Run all 10 `games` tasks in one Pi/Chakra session

## Critical: do NOT paste the full FORGED file

Pasting all 10 PRDs at once makes weaker models refuse (“only task 1 / too big”).
Paste the **thin runner** instead; the agent reads one task section at a time.

## 1. Start agent

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen\harness\chakra
pi
```

## 2. Paste ONLY this file

`artifacts/datagen_task_bank/by_category/games/PI_MARATHON_RUNNER.md`

(Not `CHAKRA_PASTE_ALL_10_FORGED.md` — that stays on disk as the PRD source.)

There is **no time limit**. If the model stops after task 1, nudge:
`Continue task 02 now. Read ## Task 02 from CHAKRA_PASTE_ALL_10_FORGED.md. Do not stop.`

See `WHY_MARATHON_FAILS.md` for the diagnosis.

## 3. Stats website

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen
python -m prompt_stats serve
```

Open **http://127.0.0.1:8787/** (Agent → pi).

## 4. Optional: re-forge / pipeline

```powershell
python scripts/run_task_bank_category.py games
```
