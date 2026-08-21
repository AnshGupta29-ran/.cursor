# VARIANT v14_java_security-auditor_multi-tenant-isolation - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `java`
- **user_persona**: `security_auditor`
- **novelty_hook**: `multi_tenant_isolation`
- **ui_surface**: `mobile_web`
- **persistence**: `localstorage`
- **complexity**: `hard`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `java`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v14_java_security-auditor_multi-tenant-isolation`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v14_java_security-auditor_multi-tenant-isolation` when demoable.

---

## BASE PRD (honor unless mutated above)

# Project Request: HivePulse — Offline Anomaly Flagger for Backyard Beekeepers

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `cli_tui`
- **persistence:** `json_file`
- **complexity:** `low`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.


## Target users & jobs-to-be-done

- **Solo beekeeper (primary persona, no ML background):** "Tell me *when* my hive behaved strangely this month so I know which day to inspect."
- Jobs: load a datalogger CSV → run detection → see flagged windows in plain language ("weight dropped 2.3σ on 2024-05-11 14:00") → view a terminal plot → export a JSON report to review later or share with a mentor beekeeper.

## Core requirements / entities

- **MetricSeries**: parsed CSV (timestamp column + one numeric metric column), with ingest metadata (row count, rejected rows, time range).
- **AnalysisRun**: one detection execution — input file, detector used (`zscore` | `iqr`), threshold, preset name, timestamp of run, resulting windows.
- **AnomalyWindow**: start/end timestamps, detector, peak score, direction (`spike` | `drop`), sample count, human-readable reason string.
- **ThresholdProfile (preset)**: named configs, e.g. `nectar-flow` (sensitive, z ≥ 2.0), `winter-cluster` (conservative, z ≥ 3.5), `custom`.

## Major feature areas

1. **Ingest & validate CSV** — auto-detect timestamp + metric columns by header name or position; reject missing headers, non-numeric metric values, empty files; skip-and-count malformed rows; sort by timestamp; dedupe exact duplicate timestamps (keep first); report an ingest summary.
2. **Detection engines (stdlib `statistics` only)** —
   - `zscore`: flag points where |z| ≥ threshold (global mean/stdev; handle stdev == 0 by returning zero anomalies, never crash).
   - `iqr`: flag points outside [Q1 − k·IQR, Q3 + k·IQR], k configurable (default 1.5).
   - Consecutive flagged points merge into one **AnomalyWindow**.
3. **Terminal plot** — ASCII/Unicode line plot of the series with anomaly points rendered as a distinct glyph (`◆` or `*`), axis labels, and a legend; width adapts to terminal (sensible 80-col default).
4. **Detector comparison view** — run both detectors, show counts and which windows agree/disagree, so the user can sanity-check sensitivity.
5. **Export & history** — write flagged windows + run summary to a JSON report file; append every AnalysisRun to a local JSON history file; `history` command lists past runs.
6. **Interactive TUI menu + one-shot flags** — a numbered menu (`load / detect / plot / compare / export / history / quit`) and equivalent CLI args (`python -m hivepulse data.csv --detector zscore --threshold 3 --plot --export out.json`) for scripted use.

## Domain workflows

**Happy path:** user runs with the bundled sample `examples/hive_weight_may.csv` (contains a seeded swarm-event drop) → ingest summary prints → z-score run flags 2 windows → plot shows the drop → export writes `report.json` → run appears in history.

**Edge cases that must not crash:** empty CSV; header-only CSV; single row; constant series (stdev 0); unsorted timestamps; duplicate timestamps; blank/whitespace metric cells; non-numeric garbage rows (skipped with count); CSV with extra columns; very short series (< 4 points → warn that IQR is unreliable, still run). Each failure mode prints a **distinct message**: validation errors vs. detection errors are worded differently.

## Data & persistence

- All persistence is **local JSON files** in a data dir (default `./hivepulse_data/`, overridable): `history.json` (list of AnalysisRuns) and user-named report exports.
- No database, no network, no model weights. Schemas documented in README.

## UX surface expectations

- First run with no args prints a guided hint pointing at the sample CSV.
- Plain-beekeeper language in output ("possible swarm event — weight drop") alongside the numeric score; never raw stat-speak only.
- Synchronous, sub-second on a 10k-row CSV; state that expectation in README.

## Quality, security, reliability

- Deterministic output for a fixed input (no wall-clock leakage into results).
- Graceful `KeyboardInterrupt` exit; no tracebacks for user-input errors.
- Path handling via `pathlib`; refuse to overwrite an existing export unless `--force`.

## Documentation & testing

- **README** (single-run delivery): what it is, the stdlib-only constraint and why, quickstart (`python -m hivepulse examples/hive_weight_may.csv --detector zscore --plot`), menu walkthrough, JSON schemas, preset table, **Limitations** (global-not-rolling stats, univariate only, assumes roughly regular sampling, not veterinary advice), and how to extend (rolling z-score) later.
- **Smoke tests only** (`pytest` or stdlib `unittest`): fixture CSVs covering happy path, empty file, constant series, malformed rows; assert both detectors return expected window counts and that export JSON is valid and loads. Tests must run in seconds with no downloads.

## Constraints & non-goals

- Stdlib-only; no third-party packages, no pip install step beyond pytest (or use unittest to avoid even that).
- Univariate only; no multivariate correlation, no forecasting, no ML training, no live sensor streaming, no GUI, no multi-user anything.
- Not a generic "data science toolkit" — all copy and presets stay in beekeeping vocabulary.

## Acceptance criteria

- [ ] `python -m hivepulse examples/hive_weight_may.csv --detector zscore --plot --export report.json` runs clean and flags the seeded swarm event.
- [ ] IQR and z-score detectors both work; comparison view shows agreement/overlap.
- [ ] ASCII plot renders with anomaly markers in an 80-col terminal.
- [ ] Malformed/empty/constant/unsorted inputs produce clear, distinct messages — zero tracebacks.
- [ ] `report.json` and `history.json` match the documented schemas.
- [ ] Smoke tests pass via one command documented in README.
- [ ] README includes quickstart, schemas, presets, and limitations.

## Uniqueness / anti-clone constraints

- This is **not** a generic "anomaly detection dashboard." Forbid placeholder UIs, lorem-ipsum sample data, and tutorial-style "metrics.csv" demos — the sample dataset must be a plausible hive-weight series with a narrated swarm event.
- Beekeeping terminology is mandatory in output strings and README (swarm, nectar flow, brood, hive scale).
- Do not relax the stdlib-only constraint; do not add server/API/web layers.
