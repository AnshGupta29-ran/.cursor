# `.cursor` workspace

Personal Cursor workspace + **agent datagen / harness** work. This is a **monorepo-style dump** of the local `~/.cursor` tree: Cursor config/skills, demo apps built during sessions, and the main research project **`headless_harness_datagen`**.

If you only care about the autonomous coding harness and task bank, jump here:

→ **[`headless_harness_datagen/`](headless_harness_datagen/)** — start with [`headless_harness_datagen/README.md`](headless_harness_datagen/README.md)

---

## Quick map (where is …?)

| Looking for | Path |
|-------------|------|
| **Harness (Chakra agent runtime)** | [`headless_harness_datagen/harness/chakra/`](headless_harness_datagen/harness/chakra/) |
| **Python supervisor / pipeline** | [`headless_harness_datagen/main.py`](headless_harness_datagen/main.py), [`headless_harness_datagen/controller/`](headless_harness_datagen/controller/) |
| **Datagen task bank (seeds + forged prompts)** | [`headless_harness_datagen/artifacts/datagen_task_bank/`](headless_harness_datagen/artifacts/datagen_task_bank/) |
| **Forged platform prompts (paste into Chakra)** | `headless_harness_datagen/artifacts/datagen_task_bank/by_category/<category>/forged/` |
| **Marathon / polish runner prompts** | `…/by_category/<category>/PI_MARATHON_RUNNER.md` |
| **Built task demos (ai_ml / games)** | [`headless_harness_datagen/harness/chakra/task_*`](headless_harness_datagen/harness/chakra/) |
| **Cursor Agent Skills** | [`skills-cursor/`](skills-cursor/) |
| **Cursor hooks** | [`hooks/`](hooks/), [`hooks.json`](hooks.json) |
| **Standalone demo apps** | Root siblings: `backend/`, `reviewhub/`, `smart-home-dashboard/`, … |
| **Root `main.py`** | Console **Minesweeper** only (not the harness) |

---

## What’s in this repo?

### 1. Main project — `headless_harness_datagen/`

Autonomous **headless harness** around **Chakra** (coding agent): plan → implement → verify → repair, with a Python supervisor, prompt forge, and a large **category task bank** for datagen.

```text
headless_harness_datagen/
├── main.py                 # Run harness against an objective
├── controller/             # Session health, conversation config
├── prompt_forge/           # Seed → category → PLATFORM ADD-ON prompt
├── prompt_stats/           # Session metrics / local UI
├── verification/           # Verify prompts & reporting
├── scripts/                # Task bank forge / diversify / paste helpers
├── docs/                   # PROJECT_GUIDE, HANDOVER, DEBUGGER, …
├── artifacts/
│   └── datagen_task_bank/
│       └── by_category/    # One folder per domain (see below)
└── harness/
    └── chakra/             # Chakra CLI + working copies of built tasks
```

**Category folders** under `artifacts/datagen_task_bank/by_category/`:

| Category | Typical contents |
|----------|------------------|
| `ai_ml` | Seeds, forged prompts, `PI_MARATHON_RUNNER.md`, polish runners |
| `games` | Same layout for game tasks |
| `cms_content`, `ecommerce`, `devops_infra`, … | Same pattern for other domains |

Inside a category you usually see:

- `*.md` / `*.json` — task seeds  
- `forged/NN_<category>_…/platform_prompt.md` — full paste prompt for Chakra  
- `PI_MARATHON_RUNNER.md` — run tasks 01→10 in one session  
- `HOW_TO_RUN_ALL_10.md` / paste batches when present  

**Task products** (apps the agent built while forging) live under the Chakra cwd:

```text
headless_harness_datagen/harness/chakra/
├── task_ai_ml_01 … task_ai_ml_10
├── task_games_01 … task_games_10
├── levellens / meritlens / …   # named demos from some tasks
├── CLAUDE.md                   # Chakra session rules for datagen
└── .chakra-profile.json        # Local Chakra profile (may be gitignored)
```

Deeper docs: [`headless_harness_datagen/README.md`](headless_harness_datagen/README.md) · [`docs/PROJECT_GUIDE.md`](headless_harness_datagen/docs/PROJECT_GUIDE.md) · [`docs/HANDOVER.md`](headless_harness_datagen/docs/HANDOVER.md)

---

### 2. Standalone demos (repo root siblings)

Apps built in Cursor sessions; **not** required to run the harness.

| Folder | What it is |
|--------|------------|
| [`backend/`](backend/) | Node API (auth / cart / products style demo) |
| [`reviewhub/`](reviewhub/) | Collaborative code-review platform |
| [`smart-home-dashboard/`](smart-home-dashboard/) | FastAPI + React smart-home simulator |
| [`social-platform/`](social-platform/) | Social API (REST + WebSocket) |
| [`taskflow/`](taskflow/) | Task / workflow style app |
| [`tower-defense/`](tower-defense/) | Unity tower-defense project |
| [`whiteboard/`](whiteboard/) | Real-time collab whiteboard (React + Node) |
| [`harness/`](harness/) | Extra / older harness scratch (prefer `headless_harness_datagen/harness`) |

---

### 3. Cursor IDE / agent config

| Path | Role |
|------|------|
| [`skills-cursor/`](skills-cursor/) | Built-in Agent Skills (automate, create-rule, canvas, …) |
| [`hooks/`](hooks/) · [`hooks.json`](hooks.json) | Cursor hooks |
| [`agents/`](agents/) | Agent-related config |
| [`plugins/`](plugins/) | Plugin cache |
| [`projects/`](projects/) | Per-workspace Cursor data (transcripts, terminals, MCP descriptors) |
| [`ai-tracking/`](ai-tracking/) | Local AI code-tracking DB |
| [`extensions/`](extensions/) | Local VS Code/Cursor extensions (**not pushed** — binaries >100MB) |
| [`argv.json`](argv.json) · [`ide_state.json`](ide_state.json) | IDE settings snapshots |

---

### 4. Root odds and ends

| Path | Note |
|------|------|
| [`main.py`](main.py) | Console Minesweeper (`python main.py`) — unrelated to harness |
| [`package.json`](package.json) | Root JS lockfile leftovers |
| [`.chakra-profile.json`](.chakra-profile.json) | Chakra env/profile at workspace root (if present) |

---

## Suggested navigation for a newcomer

1. Read **this** README (you are here).  
2. Open **`headless_harness_datagen/README.md`** for how to run the harness.  
3. Browse **`artifacts/datagen_task_bank/by_category/`** for domains.  
4. Open a forged prompt:  
   `artifacts/datagen_task_bank/by_category/ai_ml/forged/02_…/platform_prompt.md`  
5. Find the built demo under  
   `harness/chakra/task_ai_ml_02/` (or `levellens` / `meritlens` when named that way).  
6. Treat root siblings (`reviewhub`, `whiteboard`, …) as **optional demos**, not part of the harness pipeline.

---

## Related GitHub remotes

| Remote | Contents |
|--------|----------|
| https://github.com/AnshGupta29-ran/.cursor | This full workspace (minus `extensions/`, `node_modules/`, `.env`) |
| https://github.com/AnshGupta29-ran/headless_harness_datagen | Harness project alone (also nested here under `headless_harness_datagen/`) |

---

## What is *not* in git

- `node_modules/`, `.venv/`, `.env`  
- `extensions/` (oversized native binaries)  
- Nested git history for `headless_harness_datagen` was folded into this repo; use the remotes above for history/clones  

---

## License / status

Personal research + datagen workspace. Expect incomplete task demos, experimental scripts, and Cursor session artifacts under `projects/`. Prefer `headless_harness_datagen/docs/` for operational truth on the harness.
