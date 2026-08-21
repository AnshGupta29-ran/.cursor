# VARIANT v23_csharp_open-source-maintainer_multi-tenant-isolation - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `csharp`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `multi_tenant_isolation`
- **ui_surface**: `html_canvas`
- **persistence**: `csv_files`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `csharp`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v23_csharp_open-source-maintainer_multi-tenant-isolation`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v23_csharp_open-source-maintainer_multi-tenant-isolation` when demoable.

---

## BASE PRD (honor unless mutated above)

# PLATFORM PROMPT — Holdfast Retention Workbench

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `excel_workbook`
- **persistence:** `json_file`
- **complexity:** `hard`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.


## 1. Project Request / Product identity

Build **Holdfast Retention Workbench**: a membership-lapse (churn) triage tool for **independent makerspaces and tool libraries**. Our user is a non-technical membership coordinator who lives in Excel, not in dashboards. They hand the system a CSV export of member activity; a background worker trains a small scikit-learn model and produces **one Excel workbook that is the entire user interface**: a tiered "who may lapse" list, plain-language reasons, feature importances, and a run history they can trust.

Plain-language framing for the team: this is not a generic ML demo. Every label, column, and message must speak makerspace ("fob entries", "shop nights attended", "tool checkouts", "orientation completed", "dues current"), never "Telco" or tutorial boilerplate.

## 2. Target users & primary jobs-to-be-done

- **Membership coordinator (primary, non-technical):** "Every Monday, give me a Red/Amber/Green list of members likely to lapse, with reasons I can act on, in the spreadsheet I already use."
- **Board member (secondary):** "Show me which factors drive lapsing so we can fix programs, not just chase people."

## 3. Core requirements / entities (persisted as JSON files)

- `TrainingJob` / `ScoringJob`: id, status (`queued|running|succeeded|failed`), submitted_at, finished_at, input reference, error detail.
- `RunRecord`: run id, job ids, row counts, holdout metrics (accuracy, precision, recall, ROC-AUC), model type, thresholds used.
- `ModelRegistry`: current model artifact path (joblib file), training metadata JSON alongside it.
- `MetricsRegistry`: counters/timers backing the metrics endpoint (jobs processed, failures, last train/score durations, last run timestamps).

## 4. Major feature areas

- **Ingestion & validation:** Accept a member-activity CSV. Required columns documented (e.g., `member_id, tenure_months, fob_entries_30d, shop_nights_90d, tool_checkouts_90d, orientation_completed, dues_current, lapsed`). Validate presence of columns, numeric coercion per-column, minimum row count (≥40) and both classes present for training. Reject with a clear, human-readable reason — never a traceback.
- **Training:** scikit-learn `Pipeline` (median imputation for numerics, most-frequent + one-hot for categoricals) feeding LogisticRegression *or* RandomForest, selected via the workbook **Config** sheet. Fixed `random_state` for reproducibility. Stratified holdout split; record metrics on the holdout.
- **Scoring:** Score rows from a scoring CSV or the workbook's `Score_Input` sheet. Output `churn_probability` plus tier: **Red/Amber/Green** using thresholds editable in Config, plus three named threshold presets (`quiet`, `balanced`, `aggressive_outreach`).
- **Explainability:** Global top-N feature importances (coefficients or impurity-based, documented) **and** per-member top 3 contributing factors rendered as short phrases (e.g., "very few fob entries in last 30 days", "no shop nights in 90 days"). No raw coefficient dumps aimed at coordinators.
- **Observability (novelty requirement):** Structured JSON-lines log (`logs/holdfast.log`, one object per line: timestamp, level, event, job_id, duration_ms, detail) **and** a `GET /metrics` endpoint returning JSON counters/timers from `MetricsRegistry`, plus `GET /healthz`.

## 5. Domain-specific workflows

**Happy path:** Coordinator runs `POST /jobs/train` with `examples/sample_members.csv` → worker trains, evaluates, registers model, regenerates the workbook → coordinator pastes this week's active members into `Score_Input` (or posts a scoring CSV) → `POST /jobs/score` → workbook `Risk_Register` sheet now shows member_id, probability, tier, top-3 reasons, sorted Red-first. Coordinator filters Red and starts outreach.

**Edge cases (must all be handled gracefully):**
- Missing required column → job fails with message naming the missing column; reflected in API response, job record, and a workbook status note.
- Non-numeric junk in a numeric column → offending rows quarantined with reasons; job proceeds if enough clean rows remain, else fails clearly.
- Fewer than 40 rows, or zero lapsed examples → refuse training with a friendly explanation ("We need examples of members who lapsed to learn from").
- Unseen category or extra columns at scoring time → ignore extras, bucket unseen categories, note the count in the log; never crash.
- Scoring requested before any model exists → 409-style error with guidance.
- Empty or corrupt/undecodable CSV → clean validation failure, no partial writes.

## 6. Data & persistence expectations

JSON files only — **no database**. Suggested layout: `data/jobs.jsonl` (append-only), `data/runs.json`, `data/metrics.json`, `data/models/` (joblib artifact + `model_meta.json`), `logs/holdfast.log`, `output/holdfast_workbook.xlsx`. Writes must be atomic (temp file + rename) so a crash mid-run never corrupts state. The workbook is regenerated from the latest successful run, never hand-edited by the app.

## 7. UX / API surface expectations

**The Excel workbook is the UI** (build with openpyxl). Required sheets, all populated from real runs (no placeholders):
1. `Start_Here` — what this file is, last run summary, what to do next, in plain language.
2. `Config` — model choice, tier thresholds, preset profiles; read on the next run.
3. `Score_Input` — where coordinators paste new rows; headers pre-filled.
4. `Risk_Register` — scored members: id, probability, tier, top-3 reasons, conditional-format-style tier coloring.
5. `Feature_Importances` — ranked table + a native Excel bar chart.
6. `Run_History` — run id, timestamp, rows, holdout metrics, status, duration.

**API (FastAPI, Python 3.10+):** `POST /jobs/train`, `POST /jobs/score`, `GET /jobs/{id}`, `GET /runs`, `GET /healthz`, `GET /metrics`. Errors return `{ "error": "...", "hint": "..." }` with correct status codes. The **worker** is a separate process that polls the JSON job queue and does all training/scoring/workbook work; the API stays fast and never blocks on model training. Include a one-command way to run both (e.g., `make demo` or a small launcher script) and a CLI fallback (`python -m holdfast.train ...`) so the system is usable without the server.

## 8. Quality, security, and reliability

Deterministic results across reruns of the same fixture (fixed seeds). No unhandled exceptions on malformed input. Reject non-CSV uploads and path traversal attempts. Keep runtime snappy: full train+score+workbook cycle on the fixture must complete in seconds on CPU. Only light pip deps: scikit-learn, pandas, numpy, openpyxl, fastapi, uvicorn, pytest, httpx. **No** torch/cuda, no downloads, no network calls at runtime.

## 9. Documentation & testing

README (written for a non-technical reader first, engineer second): what it does, quickstart, sample `curl` commands, the two fixture CSVs (one valid, one broken-for-demo), workbook tour, limitations (small-data uncertainty, correlation ≠ causation, bias warning), and how to swap in a real CSV. Tests: **unit** (CSV validation, tiering/threshold logic, reason-phrase generation, JSON store atomic write, metrics counters) plus one **smoke test** (train on fixture → score fixture → assert workbook exists with all six sheets and a non-empty Risk_Register → healthz/metrics respond). All tests must pass quickly offline; nothing slow may block `VERDICT: PASS`.

## 10. Constraints & non-goals

No deep learning, no model training from scratch beyond the two sklearn estimators, no auth/multi-user, no web UI (the workbook *is* the UI), no streaming/real-time, no MLOps platform features.

## 11. Acceptance criteria

- [ ] `POST /jobs/train` on the fixture CSV succeeds; worker produces a registered model + run record with holdout metrics.
- [ ] `POST /jobs/score` returns tiered probabilities with per-member reason phrases.
- [ ] Workbook regenerates with all six sheets populated; `Feature_Importances` includes a bar chart; `Risk_Register` is sorted by risk.
- [ ] Config-sheet thresholds and presets actually change tier assignments on the next run.
- [ ] Each edge case in §5 fails (or quarantines) with a clear, non-technical message — nothing crashes.
- [ ] `GET /metrics` returns real counters that increment after runs; log lines are valid JSON objects.
- [ ] Same fixture re-run yields identical probabilities (deterministic seed).
- [ ] Unit + smoke tests pass; README quickstart works end to end; limitations documented.

## 12. Uniqueness / anti-clone constraints

Forbidden: any "Telco/IBM churn" language or column names; a generic "customer churn dashboard"; placeholder or empty sheets; hard-coded predictions or importances; a bare `print(accuracy)` script posing as a product. Required: makerspace-domain terminology everywhere a human reads; the workbook as a genuinely usable coordinator tool; worker+API separation; JSON-file persistence; structured logs + metrics endpoint.
