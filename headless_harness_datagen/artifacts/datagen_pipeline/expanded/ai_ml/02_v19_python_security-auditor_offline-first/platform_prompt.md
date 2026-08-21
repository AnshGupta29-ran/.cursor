# VARIANT v19_python_security-auditor_offline-first - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `python`
- **user_persona**: `security_auditor`
- **novelty_hook**: `offline_first`
- **ui_surface**: `cli_tui`
- **persistence**: `localstorage`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `python`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v19_python_security-auditor_offline-first`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v19_python_security-auditor_offline-first` when demoable.

---

## BASE PRD (honor unless mutated above)

# EpochLedger — Offline-First ML Experiment Journal with Champion/Challenger Gates

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `react_spa`
- **persistence:** `memory_only`
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


## 1. Project request / product identity
I'm the PM for a small applied-ML tooling effort. I want **EpochLedger**: a local-first experiment tracking workbench for solo practitioners and tiny teams tuning classifiers on their own machines. It runs **fully offline — no accounts, no cloud calls, no external model downloads**. Its signature workflow is **champion vs. challenger**: every experiment pins a champion run, and each new run gets an instant **promotion-gate verdict** with a plain-English explanation a non-ML stakeholder can read aloud in a standup.

Stack (locked): **Python 3.10+ FastAPI backend**, **React SPA (Vite)** frontend, **in-memory persistence only** — all state lives in process memory and is wiped on restart.

## 2. Target users & jobs-to-be-done
- **Applied ML tinkerer (primary):** log sweep runs from a training script via REST, compare results, decide the next experiment.
- **Non-ML PM/tech lead (secondary):** open the UI, read verdict cards, understand which "knob" mattered — without reading raw JSON.

Jobs: record runs with zero infrastructure; know instantly whether a run beats the champion; inspect metric curves with instability flags; fetch run artifacts (e.g., a classification report) from the browser.

## 3. Core entities
- **Experiment**: id, name, created_at, champion_run_id, gate_policy
- **Run**: id, experiment_id, name, status (`RUNNING|FINISHED|FAILED`), tags, params `{key: str|number|bool}`, metrics `{key: [{step, value}]}`, started_at/finished_at
- **GatePolicy**: primary_metric, min_delta_pct, guard_metric, guard_max_regress_pct
- **Artifact**: id, run_id, name, content_type, bytes (≤1MB), created_at
- **ApiCallEntry**: timestamp, method, path, status, latency_ms (ring buffer, last 100)

## 4. Major feature areas
- **Tracking REST API** (all under `/api/`): create/list experiments; start run; `POST /runs/{id}/log-batch` (params + metric points); finish/fail run; tag run; get run/experiment.
- **Promotion gate & verdicts**: `PUT /experiments/{id}/champion` (run + policy); `GET /runs/{id}/verdict` returns `PASS | REGRESSED | INCONCLUSIVE` (missing metric, failed run, or no champion) plus a human-readable summary string, computed server-side.
- **Compare view**: up to 4 runs side-by-side; param differences highlighted; metric deltas vs. champion; verdict chips. `GET /experiments/{id}/compare?run_ids=…`.
- **Metric curve analysis**: per-metric step series, multi-run overlay; deterministic instability detection (point deviates >3× rolling median-absolute-deviation → "instability near step k"), shown as curve notes.
- **Parameter influence panel**: rank-correlate each numeric param with the primary metric across FINISHED runs (Pearson over ranks, stdlib only — no scipy); top-3 drivers in plain English; requires ≥4 runs, else a helpful empty state.
- **Artifacts**: upload/download/preview (text, JSON, CSV) held in memory; caps 1MB per artifact, 25MB per run; `413` on overflow; slugified names (no path tricks).
- **API activity log**: last 100 requests with status and latency, visible at `/activity`.
- **Deterministic demo seed**: `POST /api/demo/seed` (and a UI button) creates experiment `sentiment-sweep` with 8 finished runs (fixed RNG seed, analytically generated curves — no training, no downloads), champion pinned. Idempotent: seeding twice returns the existing experiment.

## 5. Domain workflows
**Happy path (UI):** seed → open experiment → read verdict cards → compare champion vs. best challenger → check influence panel → upload a classification-report artifact → preview it.
**Happy path (API):** curl: create experiment → start run → log-batch → finish → `GET /verdict` → `PASS`.
**Edge cases:** logging to a FINISHED run → `409`; NaN/inf metric value → `422`; unknown ids → `404`; verdict with no champion → `INCONCLUSIVE` + guidance text; identical configs in compare → "identical configs" note; deleting the champion clears the gate; all errors use the envelope `{"error": {"code", "message"}}`.

## 6. Data & persistence
Memory only: module-level dict stores (a lock is fine). No SQLite, no disk writes, artifact bytes live in RAM. Restart wipes everything — state this in the README **and** as a persistent UI badge ("In-memory workspace — resets on restart"). Seed data must be deterministic for reproducible demos and tests.

## 7. UX / API surface expectations
React SPA routes: `/experiments`, `/experiments/:id` (runs table, champion banner, influence panel), `/experiments/:id/compare`, `/runs/:id` (curves, params, artifacts, verdict), `/activity`. Distinct loading, empty, validation-error (4xx), and server-error (5xx) states. Charts: a lightweight chart lib already declared in package.json, or hand-rolled SVG — no heavy dashboard frameworks. `GET /api/health` for liveness; CORS open to the dev server; bind 127.0.0.1.

## 8. Quality, security, reliability
Validate all inputs (param types, finite metric numbers, size caps, slugified artifact names). Single local user → **no auth**. Never eval uploaded content. Non-seed endpoints respond <100ms on demo data. **Runtime pass matters**: the app must actually boot and serve real responses, not just contain plausible code.

## 9. Documentation & testing
README: **one-command startup** (`./dev.sh` or `make dev` launching uvicorn on :8000 and Vite on :5173 with proxy, printing URLs), a copy-paste curl walkthrough (create → log → verdict), endpoint table, limitations (memory-only, single process, no auth, browser previews for text artifacts only), and a 3-line `requests` snippet showing how a real training script integrates. Tests: pytest **unit tests** for verdict logic, rank correlation, instability heuristic, and input validation; plus a **smoke test** (`scripts/smoke.py` or `pytest -m smoke`) that boots the server on a test port and asserts health → seed → log run → `PASS` verdict. All tests fast, offline, deterministic; nothing may require network, GPUs, or model weights.

## 10. Constraints & non-goals
No training or running real models in-harness; no torch/sklearn/transformers installs; no database or file persistence; no multi-user auth; no model registry/serving (this is not full MLflow); no cloud calls at runtime. A partial scaffold may already exist — reconcile and extend it rather than rewriting working code.

## 11. Acceptance criteria
- [ ] `./dev.sh` (or equivalent single command) brings up API + SPA locally
- [ ] Demo seed produces a browsable `sentiment-sweep` experiment with 8 deterministic runs and a pinned champion
- [ ] A run logged via the documented curl flow returns a structured verdict with a plain-English summary
- [ ] Verdict states `PASS`/`REGRESSED`/`INCONCLUSIVE` all reachable and correct per the gate policy
- [ ] Compare view highlights param differences and metric deltas vs. champion
- [ ] Influence panel lists top-3 param drivers (or the correct empty state)
- [ ] Metric curve shows at least one instability flag on seeded data
- [ ] Artifact upload → preview → download round-trips; oversize rejected with `413`
- [ ] Invalid inputs return the JSON error envelope; app never crashes on partial/empty payloads
- [ ] Unit + smoke tests pass offline; UI badge and README document memory-only behavior

## 12. Uniqueness / anti-clone constraints
The product is **EpochLedger** with champion/challenger promotion-gate vocabulary throughout — do not genericize it into a CRUD runs table. Plain-English verdicts and the deterministic `sentiment-sweep` seed are mandatory. Forbidden: todo-app mechanics, "Hello World" or Lorem-ipsum UI, unlabeled stub endpoints, or copying MLflow's branding. UI copy must use ML-authentic terms (epoch, F1, learning rate, champion, gate) written so a non-ML PM can follow them.

-- implement and complete all phases wihtout stopping in between , make decisions yourself and run the final platfrm in browser for me.
