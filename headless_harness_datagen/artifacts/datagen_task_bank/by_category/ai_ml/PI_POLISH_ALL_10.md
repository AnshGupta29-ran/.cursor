# PASTE INTO CHAKRA — ai_ml polish pass (tasks 01–10)

You claimed all 10 DONE. Audit shows several are missing, CLI-only stubs, API-only, or not dimension-faithful with working demos. Do a **polish / rebuild pass**. No questions. No plan-only. Ignore “Stop hook error” (that is auto-continue).

## Locked dimensions (must honor; do not homogenize)
| # | complexity | UI lock | persistence | notes |
|---|------------|---------|-------------|-------|
| 01 | medium | html_canvas | sqlite | LevelLens / resume analyzer |
| 02 | hard | react_spa | memory_only | ML experiment tracker |
| 03 | low | desktop_window | localstorage | MeritLens (already strong — light polish only) |
| 04 | hard | static_html | csv_files | ClerkLens |
| 05 | medium | api_only | sqlite | Harborline — keep API + **operator console** that calls live API |
| 06 | hard | excel_workbook | json_file | Holdfast — workbook artifact + thin ops UI to trigger jobs |
| 07 | medium | mobile_web | postgres_optional | FAQ embedding search |
| 08 | low | static_html | memory_only | OCR receipt extractor |
| 09 | hard | game_loop_window | sqlite | Toxicity filter — real window/game-loop or rich interactive canvas |
| 10 | low | cli_tui | json_file | HivePulse — CLI is OK; add optional tiny static viewer only if easy |

## Hard quality bar (every task)
- **Not DONE** if: blank page, upload-does-nothing, README-only, single unstyled form, API with no way to exercise it, claimed React/Go/Rust but empty folder.
- Seeded demo data + one-command run in README.
- Primary happy path works in ≤2 minutes without reading source.
- Match complexity: low = thin but working; medium = multi-panel; hard = fuller acceptance + richer UI when not cli/api-locked.

## Work order
For N = 01 → 10:
1. Open ONLY: `...\ai_ml\forged\NN_*\platform_prompt.md`
2. Inspect `harness/chakra/task_ai_ml_NN/` (or meritlens / levellens for 03/01).
3. If missing or below bar: rebuild/polish under `task_ai_ml_NN/` (keep existing good code when possible).
4. Start the demo, smoke the happy path, fix until it works.
5. Print: `DONE polish_N: <title> — URL or CLI + what works`
6. Immediately continue to N+1.

## Known gaps to fix first
- **01**: ensure `task_ai_ml_01` or `levellens` runs with canvas/charts UI on a browser URL.
- **02**: folder missing — implement full React SPA experiment tracker.
- **04/05**: raise to PRD depth if still thin; 05 console must classify/route live.
- **06**: Excel workbook deliverable must generate; add minimal web/ops page to train/score if missing.
- **07**: Go + mobile_web UI must run in browser.
- **08**: static HTML OCR demo must extract fields from fixtures.
- **09**: Rust project must be more than Cargo.toml — runnable interactive surface.
- **10**: CLI demo must detect anomalies on fixtures; optional HTML report ok.

## Forbidden
- Loading whole `CHAKRA_PASTE_ALL_10_FORGED.md`
- Asking for confirmation
- Leaving hung background installs/servers
- Marking DONE without a working demo path

Start now with task 01.
