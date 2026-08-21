# Langfuse setup for autopilot

Chakra gRPC does **not** push to Langfuse by itself. Autopilot does:

- one Langfuse **session** for the autopilot run
- one **trace per task** (`datagen:<task_key>`)
- **live mirror** while the task runs: turns → generations, tools → spans
- on finish: **repo** span + harness JSONL sample from
  `logs/*/pipeline/working/trace.jsonl`

## PowerShell (autopilot terminal — before re-run)

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen

pip install langfuse

$env:LANGFUSE_PUBLIC_KEY="pk-lf-..."
$env:LANGFUSE_SECRET_KEY="sk-lf-..."
$env:LANGFUSE_HOST="https://fuse.tensorstudio.ai"   # or your host
$env:OPENAI_MODEL="gpt"

python -m datagen_pipeline run-autopilot --expand-first 45 --model gpt
```

You should see:

1. `[langfuse] ON session_id=...`
2. `[langfuse] live mirror ON`
3. In the UI: session → task traces → nested generations/tool spans updating during the run

Restart autopilot after pulling these fixes (Bun gRPC can keep running).
