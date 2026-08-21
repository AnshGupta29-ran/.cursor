# ONE-COMMAND AUTOPILOT (no 130× paste)

You do **not** need to paste / mark-done 130 times. Use the headless autopilot.

## Why the last interactive run errored

`API Error: 502 Bad Gateway` from TensorStudio (`nginx`) — the **model API** dropped,
not your code. `ai_ml:02` had already finished successfully before that.
Also fixed: Stop hook wrongly auto-continued after `DONE ai_ml:02` (now stops in pipeline mode).

## Setup (two terminals)

**A — Chakra gRPC (leave running)**
```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen\harness\chakra
$env:OPENAI_MODEL="kimi3"
bun run dev:grpc
```
Wait until you see gRPC on `:50051`.

**B — Autopilot (all pending tasks, checkpointed)**
```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen
python -m datagen_pipeline run-autopilot --base-only --model kimi3
```

That loop:
1. Picks next pending task from checkpoint
2. Runs `main.py` with **one** `platform_prompt.md` (never all-10)
3. Runs deterministic **VALIDATE** (structure, language lock, smoke, seed data)
4. Marks done only if validate passes (else failed → retry)
5. Frees demo ports
6. Retries on 502/timeout
7. Continues until queue empty  
Re-run the **same** command after any crash — it resumes.

### Validate gate

```powershell
python -m datagen_pipeline validate --key cms_content:04
```

Reports land in `artifacts/datagen_pipeline/validate_reports/`.
Validated demos are indexed under `artifacts/datagen_pipeline/synthetic_exports/` for scale tracking.

Every task must ship `scripts/smoke.py` (or `npm run smoke`) + seed/fixture data.
Use `--skip-validate` only for debugging (not for synthetic scale runs).
Optional LLM Phase-7: add `--verify`.


## Scale to ~5k repos

```powershell
# Generate variant PRDs (once), then run them all:
python -m datagen_pipeline run-autopilot --expand-first 45 --model kimi3
# (omit --base-only so variants are queued)
```

## Interactive Chakra (optional)

Only if you prefer the UI: after each DONE still run `mark-done`, or just switch to autopilot.

## Langfuse (optional)

```powershell
$env:LANGFUSE_PUBLIC_KEY="..."
$env:LANGFUSE_SECRET_KEY="..."
pip install langfuse
```
