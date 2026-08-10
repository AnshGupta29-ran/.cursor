# Datagen dimensions, cost accounting, and how to run (kimi3)

This repo now tracks **synthetic agentic training dimensions**, **token/$ spend**, and a **cross-product matrix** so you can plan thousands of examples and measure cost per category.

## Where things live

| Path | Role |
|------|------|
| `datagen_dims/taxonomy.py` | Exhaustive dimension list (meta / generic / quality) |
| `datagen_dims/matrix.py` | Cross-product planner + combination catalog |
| `datagen_dims/costing.py` | Tokens → USD + compute units |
| `datagen_dims/classify.py` | Auto-assign dimensions to each prompt/session |
| `datagen_dims/stats.py` | Averages per category from `prompt_stats` ledger |
| `datagen_dims/cli.py` | `python -m datagen_dims …` |
| `artifacts/datagen_dims/` | Exported taxonomy, plans, catalogs, stats JSON |
| `prompt_stats/` | Session ledger (tokens, runtime); now stamps `dimensions` + `cost` |
| `.env` | `DATAGEN_PRICE_*` rates + `OPENAI_MODEL=kimi3` |
| `verification/prompts.py` | Harness bootstrap (compile/implement/verify lifecycle) |

### How it works at runtime

1. You run Chakra / `main.py` / forge as usual (kimi3).
2. `prompt_stats` hooks record the session (tokens, time, tools).
3. Each record is enriched with **`dimensions`** (`complexity`/`value` = `low|medium|hard`, plus task/domain/language/…) and a **`cost`** block (USD + compute units from `.env` rates).
4. `python -m datagen_dims stats` aggregates average tokens/$ **per domain / complexity×value**.
5. `python -m datagen_dims plan` computes the cross-product size and estimates spend for N examples per combo.

---

## Dimension layers

### Meta (what an agentic model is trained *for*)

- **task_family** — coding_implement, coding_debug, analysis_reason, data_visualization, spreadsheet_excel, ml_inference_eval, devops_ops, …
- **business_domain** — ecommerce, finance_fintech, gaming, iot_automation, …
- **artifact_type** — web_fullstack, backend_api, spreadsheet_workbook, game_prototype, …
- **language_runtime** — python, typescript, cpp, csharp, excel_office, mixed_polyglot, …
- **modality** (optional axis) — text_code, tabular_excel, image_vision, …
- **user_persona** (optional) — solo_dev, startup_pm, …

### Generic / harness (how the run is shaped)

- **agent_topology** — `single_agent` | `subagent_spawns` | `multi_agent_parallel` (**future**; today verification is strongest as one conversation with optional Plan/general-purpose/verification Agent spawns — full parallel multi-agent spin is a known gap)
- **tool_profile** — read_only → shell_heavy
- **verification_mode** — none | smoke_run | unit_tests | runtime_pass | human_review
- **session_shape** — single_shot | multi_turn_repair | long_horizon
- **repo_state** (optional) — empty_scratch | brownfield_large | …

### Quality (every example must have these)

- **complexity**: `low` | `medium` | `hard`
- **value** (training value): `low` | `medium` | `hard`

List everything:

```bash
python -m datagen_dims list
```

---

## Cross product → thousands of examples

**Default “core” starter axes** (~6.3k combinations):

`task_family × business_domain × language_runtime × complexity × value`

(with starter value filters on the first three axes — see `STARTER_FILTERS`)

```bash
# Count combos + estimate $ (uses avg in/out tokens)
python -m datagen_dims plan --examples-per-combo 3 --avg-in 25000 --avg-out 80000
# -> ~6,300 combos; ×3 examples = ~18,900 runs (cost estimate printed)

# Write a JSONL catalog of seeds to generate
python -m datagen_dims plan --examples-per-combo 3 --write-catalog

# Narrow further
python -m datagen_dims plan --filter "language_runtime=python,task_family=coding_implement,business_domain=ecommerce|gaming" --write-catalog
```

> Full unconstrained product of *all* harness axes is huge — use `--full` only with `--filter`.

Each catalog row has `dimensions`, `combo_id`, and a `seed_hint` you can feed to forge / `main.py`.

---

## Token / money accounting

Set real rates in `.env`:

```env
DATAGEN_PRICE_INPUT_USD_PER_M=0.50
DATAGEN_PRICE_OUTPUT_USD_PER_M=2.00
DATAGEN_COMPUTE_UNITS_PER_M=1.0
OPENAI_MODEL=kimi3
```

From recorded sessions:

```bash
python -m prompt_stats refresh
python -m datagen_dims stats
python -m datagen_dims stats --group-by language_runtime
python -m datagen_dims stats --group-by complexity
```

Ledger rows gain:

```json
"dimensions": { "complexity": "hard", "value": "medium", "task_family": "...", ... },
"cost": { "usd": 0.12, "compute_units": 0.05, "total_tokens": 90000, ... }
```

---

## Seed / prompt locations

| Location | What |
|----------|------|
| `docs/archive/project_prompts.md` | ~27 numbered + bonus + 2 long PRDs |
| `prompt.txt` | One full habit-tracker PRD |
| `prompt_forge/categories.py` | 26 short `example_seeds` |
| `prompt_forge/templates/*.md` | 13 category shapes (forge only) |
| `artifacts/forge_demo/platform_prompt.md` | Forged Tidewatch PRD |
| `artifacts/forge_image/platform_prompt.md` | Forged PalletLens PRD |
| `experiments/*/`, `harness/chakra/palletlens/` | Generated code (not seeds) |

Also: `python -m datagen_dims seeds`

---

## Step-by-step: run with Chakra + kimi3

### 0) Confirm model

`.env` and `harness/chakra/.chakra-profile.json` should have `OPENAI_MODEL=kimi3`. Restart Chakra after changes.

### 1) Start Chakra gRPC

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen\harness\chakra
bun run dev:grpc
# or: ..\..\scripts\start_chakra.sh
```

### 2a) Harness pipeline (recommended for datagen)

From repo root:

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen

# Archive-style seed + forge expansion
python main.py "Create a real-time collaborative whiteboard application using React, TypeScript, Node.js, Express, and Socket.IO." --forge-prompt --workdir wb_run1

# From prompt.txt
python main.py "$(Get-Content -Raw prompt.txt)" --workdir habit_run1

# Forced category
python main.py "Inventory for a bike shop" --forge-prompt --forge-category ecommerce --workdir ecom_run1
```

Harness owns plan → implement → verify → repair (compile/smoke inside the repo). Wall clock defaults to ~25 minutes.

### 2b) Interactive Chakra (paste a forged PRD)

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen\harness\chakra
# start interactive chakra CLI, then paste:
#   ..\..\artifacts\forge_demo\platform_prompt.md
```

### 3) Record + analyze spend

```powershell
python -m prompt_stats refresh
python -m datagen_dims stats
python -m prompt_stats serve
# open http://127.0.0.1:8787/
```

---

## Multi-agent note

The harness bootstrap already allows **Agent** subagents (Plan / general-purpose / verification). That maps to dimension `agent_topology=subagent_spawns`.

**`multi_agent_parallel` is not fully productized yet** — verification does not spin a separate peer swarm. Track it as a future axis when you extend the harness; until then generate most matrix cells with `single_agent` or `subagent_spawns`.
