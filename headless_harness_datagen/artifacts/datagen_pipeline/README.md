# Datagen pipeline (checkpointed, kimi3-safe, multi-language)

Outer loop for **ai_ml + games leftovers** and **11 untouched categories**.  
**One PRD per run.** Never paste `CHAKRA_PASTE_ALL_10_FORGED.md`.

## Fixes baked in (stall / variety)

| Issue | Fix |
|-------|-----|
| DONE `cms_content:02` never matched | Stop-hook regex + pipeline mode file |
| Hook forced next task forever | Pipeline mode: stop after DONE |
| Model default gpt-oss | `.chakra-profile.json` → `kimi3` |
| Hours wasted on low tasks | Pace rules in CLAUDE.md + thin prompts |
| Homogenized to Python | LANGUAGE LOCK banners on all 130 PRDs; locks in next prompt |
| Partials skipped | Queue starts with ai_ml/games gaps, then untouched |
| Need ~5k repos | `expand --variants-per-task 45` rotates language/UI/persona |

## Queue (base-only, already-strong skipped)

Skipped as done: ai_ml 01/03/05, games 01/02/07/08/10, cms 01.  
Pending first: `ai_ml:02`, then other ai_ml/games gaps, then cms 02…storage.

Languages in bank: python, typescript, javascript, go, rust, java, csharp, cpp, excel_office.

## Interactive loop

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen

# Restart Chakra after profile change so kimi3 loads:
#   cd harness\chakra; $env:OPENAI_MODEL="kimi3"; chakra

python -m datagen_pipeline next --base-only --model kimi3
# Paste harness/chakra/CHAKRA_NEXT_TASK.md into Chakra

# After DONE:
python -m datagen_pipeline mark-done --key ai_ml:02 --base-only
```

## Expand toward ~5000 (optional, disk-heavy)

```powershell
python -m datagen_pipeline expand --variants-per-task 45
# then omit --base-only so variants enter the queue
```

## Langfuse

```powershell
$env:LANGFUSE_PUBLIC_KEY="pk-..."
$env:LANGFUSE_SECRET_KEY="sk-..."
$env:LANGFUSE_HOST="https://cloud.langfuse.com"
pip install langfuse
```

## Headless

```powershell
python -m datagen_pipeline run-headless --base-only --model kimi3 --skip-verification --continue-on-error
```
