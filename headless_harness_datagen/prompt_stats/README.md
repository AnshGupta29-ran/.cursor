# Prompt statistics

Tracks **every prompt** related to agent work in this repo — **Chakra and Pi** —
past runs and future ones — with size, complexity, timing, models, and outcomes.

## Data location

| Path | Purpose |
|------|---------|
| `artifacts/prompt_stats/ledger.jsonl` | Append-only permanent ledger |
| `artifacts/prompt_stats/dashboard.html` | Human-readable dashboard |
| `artifacts/prompt_stats/latest.json` | Last refresh summary |

## Commands

```bash
python -m prompt_stats refresh      # backfill history + rebuild snapshot
python -m prompt_stats show         # terminal table
python -m prompt_stats dashboard    # static HTML snapshot
python -m prompt_stats serve        # interactive graphs UI (live sync)
```

Open **http://127.0.0.1:8787/** after `serve`. A hard refresh (or first load) runs a
full collect into the ledger; the UI then polls `/api/sync` so Chakra **and Pi**
session time/tokens stay current. You do **not** need a separate `collect` terminal.
Forge / `main.py` runs also append via hooks.

### Agents

| Agent | Session source on disk | Ledger `source` |
|-------|------------------------|-----------------|
| Chakra | `~/.chakra/projects/**/*.jsonl` | `chakra_session` / `chakra_model` |
| Pi | `~/.pi/agent/sessions/**/*.jsonl` | `pi_session` / `pi_model` |

Filter by **Agent** on the dashboard. Model cards show which agent used each model.

### Token display

| Field | Meaning |
|-------|---------|
| `input_tokens` / `output_tokens` | Real totals from session usage traces when present |
| `*_tokens_est` | Estimated from prompt text (~chars/4) for forge / interactive prompts |
| UI | Formats as raw counts, `1.2k`, or `1.05M` |

## What gets recorded automatically (going forward)

1. **`python -m prompt_forge forge …`** → forged platform prompt metrics
2. **`python main.py … --forge-prompt`** → forge + (on finish) pipeline runtime/verdict
3. **`python main.py …`** (any pipeline finish) → objective complexity + turns/runtime
4. **Live sync** → Chakra + Pi session wall time, tools, models, token usage

## What `refresh` backfills

- `artifacts/forge_*/forge_meta.json` and `logs/*/prompt_forge/`
- `logs/*/pipeline/summary.json` (+ trace duration when present)
- Numbered prompts in `docs/archive/project_prompts.md`
- Interactive Chakra history from `~/.chakra/`
- Pi sessions from `~/.pi/agent/sessions/`
- Generated project README titles under `experiments/` and `harness/chakra/`

## Metrics

Per prompt: chars, est. tokens, headings, acceptance checkboxes, bullets,
**complexity_score (0–100)** + band (`low` / `medium` / `high` / `very_high`).

Per agent session (when available): `runtime_seconds`, `tool_calls`,
`input_tokens` / `output_tokens`, `model`, per-model slices.
