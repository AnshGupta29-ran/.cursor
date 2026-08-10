# Category batch FORGED: ai_ml (10/10) — paste into Chakra

Each task is a forged PRD with a **locked dimension mix**. Implementing these under
`harness/chakra/task_ai_ml_NN/` produces synthetic agent trajectories for stats.

**Playing/demoing alone is NOT datagen** — datagen is the implement session.

## Dimension coverage

| # | complexity | value | language | UI | persistence | verification |
|---|------------|-------|----------|----|-------------|--------------|
| 01 | medium | medium | python | html_canvas | sqlite | unit_tests |
| 02 | hard | hard | python | react_spa | memory_only | runtime_pass |
| 03 | low | medium | typescript | desktop_window | localstorage | browser_smoke |
| 04 | hard | hard | python | static_html | csv_files | visual_diff |
| 05 | medium | low | javascript | api_only | sqlite | unit_tests |
| 06 | hard | hard | python | excel_workbook | json_file | runtime_pass |
| 07 | medium | medium | go | mobile_web | postgres_optional | browser_smoke |
| 08 | low | medium | python | static_html | memory_only | static_pass |
| 09 | hard | hard | rust | game_loop_window | sqlite | runtime_pass |
| 10 | low | low | python | cli_tui | json_file | static_pass |

Honor each task’s dimensions. **Do not** rewrite every task to the same stack.
Depth bands control fidelity/effort: **low** = thin + simple visuals; **medium** = core + light tests;
**hard** = fuller acceptance + richer UI when applicable. Depth ≠ a time stop.

## Rules — mandatory

1. **No time limit / no turn cap.** Never refuse for size. Never ask for confirmation.
2. Complete tasks **01 → N in order**. Separate folder per `workdir`.
3. Plan mode OFF. Implement immediately; auto-continue between tasks.
4. After each: `DONE task_N: <title> — path + how to run`, then start the next.
5. Match Depth + UI fidelity to complexity. Low must look/feel simpler than hard.
6. README run command + smoke/test path from the PRD.

Stats: `python -m prompt_stats serve` → http://127.0.0.1:8787/ (hard-refresh).

---

## Task 01 — AI Resume Analyzer
**workdir:** `task_ai_ml_01`
**id:** `ai_ml_01_ai-resume-analyzer`
**seed (original):** Create a resume analysis web application using React, FastAPI, and a pre-trained NLP model from Hugging Face Transformers. Users should be able to upload PDF or DOCX resumes, extract structured information, identify skills, estimate experience level, and compare the resume against a provided job description. Display skill gaps, matching percentage, keyword analysis, and recommendations through an intuitive dashboard.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "ml_inference_eval", "business_domain": "data_analytics", "ui_surface": "html_canvas", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "must include a live demo mode with sample data", "delivery": "docker_compose_optional", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# LevelLens — Engineering Resume Signal & Leveling Analyzer

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product identity
Build **LevelLens**, a local-first web app that helps staff engineers and hiring-loop members screen *engineering* resumes against a target job description (JD). Unlike generic "match %" tools, LevelLens extracts **leveling signals** — scope, quantified impact, leadership verbs — and calibrates both resume and JD to an IC seniority ladder (IC3 Junior → IC7 Principal), alongside skill coverage and gap analysis. All scoring is **deterministic and auditable**: the formula lives in the README and every score traces to extracted evidence.

**Stack (locked):** Python 3.10+, FastAPI, SQLite, server-served HTML + vanilla JS with **Canvas 2D** charts. No React/npm build step (UI surface lock = html_canvas). Deps: `fastapi`, `uvicorn`, `pypdf`, `python-docx`, `pytest`, `httpx`. No torch/transformers in the default path.

## 2. Target users & jobs-to-be-done
- **Staff engineer on a hiring loop:** fast, defensible first-pass screen; wants to see *why* a score was given.
- **Engineering manager:** detect level mismatch between JD and inbound resume before scheduling interviews.
- **Candidate (secondary):** self-audit a resume against a target role.

## 3. Core entities (SQLite)
- `resume_assets`: id, filename, mime, raw_text, char_count, created_at
- `job_descriptions`: id, title, raw_text, created_at
- `analysis_runs`: id, resume_id, jd_id, mode (`live`|`demo`), match_score, seniority_band, seniority_score, skill_coverage, scores_json (full structured result incl. skill matches/gaps/evidence), duration_ms, created_at

## 4. Major feature areas
- **Ingestion:** upload PDF/DOCX/TXT (≤5 MB) or paste resume text; paste-in JD. Validate extension and extractability; reject corrupt files and image-only/scanned PDFs with a clear reason.
- **Deterministic extraction pipeline (no downloads):**
  - Skills: curated lexicon (~120+ skills, canonical aliases like `k8s`→Kubernetes) across 6 clusters: Languages, Frontend, Backend, Data/ML, Infra/DevOps, Leadership/Process.
  - Impact signals: rule/regex detection of quantified achievements (%, $, "team of N", "X users", latency/scale numbers).
  - Experience estimate: year-range and role-date heuristics.
  - Seniority score: documented weighted formula over impact count, scope verbs ("owned", "architected", "drove"), leadership terms, years → band IC3–IC7.
- **JD comparison:** pure-Python TF-IDF cosine + skill coverage → composite match score (weights documented). Skill-gap list = JD skills absent from resume, ranked by JD term frequency. JD-implied band estimated from the same seniority scorer.
- **Canvas dashboard (hand-drawn Canvas 2D, no chart libs/CDN):** (1) radar of the 6 skill clusters, resume vs JD overlay; (2) seniority gauge, resume band vs JD-implied band; (3) horizontal bars for top skill gaps.
- **Recommendations:** rule-based and evidence-linked, e.g. "JD references 'Kubernetes' 4×; absent from resume" / "1 quantified impact found; IC6+ resumes typically show 4+".
- **History & export:** past runs list + detail view; export a run as JSON or CSV.
- **Live demo mode (required):** one-click "Load demo" seeds 3 named fixture resumes (strong-senior, junior-mismatch, career-changer) + 2 JDs from `fixtures/*.txt`, runs the real pipeline through the paste path, and lands on a populated dashboard clearly labeled DEMO. Must work with zero uploads, offline.

## 5. Domain workflows
**Happy path:** upload PDF resume + paste JD → loading state → dashboard with radar/gauge/gaps, match score, band comparison, recommendations → run saved → export JSON. **Edge cases:** corrupt PDF; wrong extension; empty extraction (scanned PDF); JD < 50 chars; resume with zero lexicon hits (return valid result with empty gaps + warning, not a crash); oversized file; re-upload of same file (allowed, creates a new run).

## 6. Data & persistence
SQLite at `./data/levellens.db`, schema auto-created on startup. History must survive restart. Demo fixtures are plain-text files (no binary PDFs shipped); demo runs flow through the same analysis code as live runs.

## 7. UX / API surface
Single-page UI: intake panel, dashboard panel, history panel. Loading state disables submit; validation errors (4xx with reason codes) render differently from pipeline failures (5xx). If DB is empty, the demo CTA is the hero element. Endpoints: `POST /api/analyze` (multipart file + jd_text), `POST /api/analyze/text`, `GET /api/analyses`, `GET /api/analyses/{id}`, `GET /api/analyses/{id}/export?format=json|csv`, `POST /api/demo/seed`, `GET /api/health`. OpenAPI at `/docs`. Structured request logging (method, path, status, ms) to console.

## 8. Quality, security, reliability
Size cap + extension allowlist; typed extraction errors; same inputs → byte-identical scores; all tests offline; no secrets, single-user local tool (no auth).

## 9. Documentation & testing
README in staff-engineer voice: architecture sketch, **scoring formula with weights**, how to extend the skill lexicon, one-liner run command, sample `curl`, demo walkthrough, candid limitations (English-only lexicon, no OCR, keyword extraction limits, heuristic banding), and the optional Hugging Face path (sentence-transformers embeddings behind an env flag — documented, never required). Pytest, light: extraction units, scoring determinism, validation rejections, API happy path via TestClient, demo seed idempotency (~8 fast tests).

## 10. Constraints & non-goals
No React/npm, no chart libraries, no torch/transformers download, no LLM calls, no OCR, no multi-user auth, not an MLOps platform. Dockerfile/docker-compose optional; app must run with plain `uvicorn`.

## 11. Acceptance criteria
- [ ] Upload PDF/DOCX/TXT + JD → structured result: match score, seniority band (both sides), skill gaps, impact count
- [ ] Corrupt/unsupported/empty inputs fail with clear 4xx + UI error distinct from 5xx
- [ ] Radar, gauge, and gap bars render on `<canvas>` from API data
- [ ] One-click demo seeds fixtures and shows a populated, DEMO-labeled dashboard
- [ ] History persists across restart; JSON + CSV export succeed
- [ ] `pytest` passes offline, covering analyze happy path + validation failures
- [ ] README documents formula, limitations, and a working curl example

## 12. Uniqueness / anti-clone constraints
This must **not** be the generic "upload resume → matching %" clone: leveling-band calibration, impact-signal extraction, and evidence-linked recommendations are each mandatory and visible in the UI. Use engineering-hiring vocabulary (IC bands, scope, leveling), not generic HR copy. Scoring is deterministic and explained — no opaque black box, no placeholder panels, no lorem ipsum.

When done, print `DONE task_1: AI Resume Analyzer` and start the next task immediately.

---

## Task 02 — ML experiment tracking (MLflow-like)
**workdir:** `task_ai_ml_02`
**id:** `ai_ml_02_ml-experiment-tracking-mlflow-like`
**seed (original):** Build a machine learning experiment tracking platform similar to MLflow with experiment comparison, metric visualization, artifact storage, and REST APIs.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "resume_mid_task", "repo_state": "partial_scaffold", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "ml_inference_eval", "business_domain": "data_analytics", "ui_surface": "react_spa", "persistence": "memory_only", "testing_depth": "unit_plus_smoke", "novelty_hook": "offline-first; no cloud accounts", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# EpochLedger — Offline-First ML Experiment Journal with Champion/Challenger Gates

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


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

When done, print `DONE task_2: ML experiment tracking (MLflow-like)` and start the next task immediately.

---

## Task 03 — Automated resume screening system
**workdir:** `task_ai_ml_03`
**id:** `ai_ml_03_automated-resume-screening-system`
**seed (original):** Create an Automated Resume Screening System in Python that scores resumes against a job description using keyword/skill heuristics or a small local model, with a review queue UI.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "multi_turn_repair", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "low", "value": "medium", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "ml_inference_eval", "business_domain": "data_analytics", "ui_surface": "desktop_window", "persistence": "localstorage", "testing_depth": "integration_light", "novelty_hook": "accessibility-first keyboard UX", "delivery": "cli_entry_plus_ui", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# MeritLens — Auditable Resume Screening Workbench

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product Identity
**MeritLens** is a transparent, rubric-driven resume screening tool for **apprenticeship and skilled-trades cohort hiring** (union training centers, community-college workforce boards). Unlike black-box "AI match %" tools, every MeritLens score decomposes into named, weighted criteria a compliance officer can defend. Built in **TypeScript** (Vite + Node ≥18), delivered as (a) a **CLI** (`meritlens screen …`) and (b) a **desktop window** app (minimal Electron shell over the same renderer; renderer must also run standalone in a browser for smoke testing). All state persists in **localStorage**. No external model downloads, no network calls at runtime.

## 2. Target Users & Jobs-to-be-Done
- **Program coordinator** (enterprise buyer): "Rank 60 applicants for the Industrial Maintenance Apprentice cohort against our published rubric, in under an hour, with a paper trail."
- **Compliance reviewer**: "Show *why* each candidate was bucketed, and export the decision log for audit."

## 3. Core Requirements / Entities (localStorage namespace `meritlens.v1`)
- **RoleProfile**: name, weighted skill criteria `[{skill, synonyms[], weight}]`, section weights (certifications/experience/education), thresholds `{advance, hold}`.
- **ResumeAsset**: filename, raw text, import timestamp, validation status.
- **ScreeningResult**: resumeId, profileId, totalScore (0–100), per-criterion breakdown `{criterion, matched, evidenceSpans[], points}`, confidence (coverage-derived), matched/missing skills.
- **ReviewDecision**: resumeId, bucket (`advance|hold|reject`), decidedBy, timestamp, note.
- **AuditEvent**: append-only log of imports, scores, threshold edits, decisions.

## 4. Major Feature Areas
- **Ingestion**: paste text or upload `.txt` / `.md` resumes (multi-file); CLI accepts a folder. Unsupported/corrupt/empty files rejected with explicit reason; oversized files (>200 KB) rejected.
- **Rubric engine**: pure deterministic TypeScript; case-insensitive keyword + synonym matching, section detection, weighted sum, evidence span offsets. Same input → identical output, always.
- **Interpretation UX**: per-candidate view shows score decomposition, matched vs missing skills, and **evidence highlighting** of matched spans in the resume text.
- **Review queue**: candidates auto-bucketed into Advance/Hold/Reject by profile thresholds; human confirms or overrides every row (human-in-the-loop; nothing auto-finalizes).
- **Comparison**: side-by-side candidate-vs-job-description view (JD entered per profile).
- **Thresholds**: editable per profile with two presets (`strict`, `open-cohort`); edits logged to AuditEvent.
- **Export**: decisions + audit log as JSON and CSV.

## 5. Domain Workflows
**Happy path**: create RoleProfile (seeded sample: "Industrial Maintenance Apprentice" with OSHA-30, PLC basics, hydraulics, NCCER, blueprint reading) → import 3 sample resumes (ship as fixtures) → score → triage queue entirely by keyboard → export decision report.
**Edge cases**: zero-match resume scores 0 with "no criteria matched" explanation (never crashes); duplicate filename flagged; corrupt profile JSON in localStorage → safe reset with warning; localStorage quota error surfaced.

## 6. Data & Persistence
All entities in localStorage under one versioned key; "Export workspace" / "Import workspace" round-trips full JSON. CLI is stateless: reads files, prints ranked table, optionally writes `results.json`. No server, no database.

## 7. UX / API Surface — Accessibility-First Keyboard UX (headline feature)
- Three views: **Queue**, **Candidate Detail**, **Roles & Thresholds**. Every action operable without a mouse: `j/k` or arrows move queue selection (roving tabindex), `Enter` opens detail, `a/h/r` set bucket, `e` export, `?` opens shortcut overlay (focus-trapped, `Esc` closes, focus returns to prior element).
- `aria-live="polite"` region announces score loads and decisions ("Candidate Rivera moved to Hold"); skip-link to main; visible focus ring; WCAG AA contrast; semantic landmarks.
- Render resume text via `textContent` only (XSS-safe). Desktop window: single-file Electron `main` opening the built UI; `npm run desktop`.
- CLI: `meritlens screen --profile <file> --resumes <dir> [--json]`.

## 8. Quality, Security, Reliability
Deterministic scoring unit-tested against fixtures; no runtime network; graceful empty/partial input handling; loading state during batch scoring; validation errors distinguished from scoring errors in UI.

## 9. Documentation & Testing
- **README**: install, CLI examples, sample-data walkthrough, full keyboard map, limitations (English-only keyword heuristics, synonym bias risk, not legal/defensibility advice), how a real model could replace the rubric later.
- `npm test` — integration-light: Vitest over the engine + validation paths using fixture resumes (fast, no downloads).
- `npm run smoke` — browser smoke: build, serve, assert Queue renders and the `j`/`a` keyboard triage flow works (Playwright chromium if binaries cached; otherwise jsdom DOM smoke — document which ran; must not block PASS).

## 10. Constraints & Non-Goals
TypeScript only — **do not switch to Python** (dimension lock overrides the seed's Python mention). No PDF/DOCX parsing, no external ML APIs, no auth/multi-user, no MLOps. Legacy-messy repo: leave pre-existing files untouched; build under `src/`, `cli/`, `electron/`, `fixtures/`.

## 11. Acceptance Criteria
- [ ] `npm install && npm run dev` (or `desktop`) shows seeded profile + 3 fixture resumes scored and bucketed
- [ ] Invalid file type and empty file rejected with clear messages
- [ ] Every score shows criterion-level breakdown and highlighted evidence
- [ ] Queue fully triageable by keyboard alone; decisions announced via aria-live
- [ ] Threshold edit re-buckets candidates and writes an AuditEvent
- [ ] JSON + CSV export of decisions/audit works; CLI ranks a folder and emits JSON
- [ ] `npm test` and `npm run smoke` pass; README limitations present

## 12. Uniqueness / Anti-Clone Constraints
Not a generic "upload resume → match %" clone: must use skilled-trades terminology (journeyman, OSHA-30, NCCER, apprenticeship cohort), must expose the rubric decomposition (opaque AI scores forbidden), and must treat keyboard-first accessibility as a primary feature, not an afterthought. No placeholder UI, no lorem ipsum, no todo-app patterns.

-- implement and complete all phases wihtout stopping in between , make decisions yourself and run the final platfrm in browser for me.

When done, print `DONE task_3: Automated resume screening system` and start the next task immediately.

---

## Task 04 — AI document assistant
**workdir:** `task_ai_ml_04`
**id:** `ai_ml_04_ai-document-assistant`
**seed (original):** Build an AI Document Assistant: upload text/PDF, chunk and index locally, answer questions with citations from retrieved chunks (stub LLM OK if labeled).
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "visual_diff", "session_shape": "approval_gated", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "ml_inference_eval", "business_domain": "productivity_collab", "ui_surface": "static_html", "persistence": "csv_files", "testing_depth": "smoke_only", "novelty_hook": "deterministic --seed for reproducible runs", "delivery": "notebook_plus_script", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# ClerkLens — Cited Q&A Over Municipal Meeting Packets

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product Identity
Build **ClerkLens**, a local, single-user research assistant built by a solo civic-tech developer for reading municipal meeting records. It ingests agendas, minutes, and ordinance excerpts (`.txt`, `.pdf`), chunks and indexes them locally, and answers questions with **extractive, citation-backed answers** — every answer sentence carries chunk citations, and the system **abstains rather than hallucinates** when retrieval confidence is low. The LLM layer is a **clearly labeled deterministic stub** (template + extractive sentence selection), so the repo runs fully offline with zero model downloads; a real LLM can be plugged in later via a documented seam. Human-in-the-loop stance: all answers are *drafts with provenance*, never auto-final.

## 2. Target Users & Jobs-to-be-Done
A solo developer / local journalist / civic watchdog who asks things like *"What was the vote on the short-term rental ordinance?"* and needs to (a) get a traceable answer fast, (b) click through to the exact source passage, and (c) keep an auditable history of every question asked.

## 3. Core Entities (CSV-backed, `data/` dir, stdlib `csv` only)
- `documents.csv`: doc_id, filename, doc_type (agenda|minutes|ordinance), meeting_date, n_chars, sha256, ingested_at
- `chunks.csv`: chunk_id, doc_id, seq, start/end char, page (if PDF), text, token_count
- `queries.csv`: query_id, asked_at, question, seed, profile, top_k
- `answers.csv`: answer_id, query_id, status (answered|abstained), confidence_band, answer_text, cited_chunk_ids, latency_ms
- `request_log.csv`: ts, endpoint, status_code, ms

Deterministic IDs: `doc_id = sha256(content)[:12]`; `chunk_id = {doc_id}-c{seq:04d}`. CSVs are the source of truth; the search index is rebuilt from them at startup.

## 4. Major Feature Areas
- **Ingestion**: HTML form + CLI; validates extension, size ≤ 2 MB, non-empty extractable text. Corrupt or scanned (no-text-layer) PDFs rejected with distinct messages. Duplicate content detected via sha256 → skipped with notice, no duplicate rows.
- **Chunking**: deterministic ~450-char windows, 80-char overlap, paragraph-boundary aware; pure function of (text, seed).
- **Index/retrieval**: TF-IDF + cosine similarity (pure-Python preferred; scikit-learn allowed if pinned). Ties broken by ascending chunk_id for stability.
- **Answer composer (STUB — labeled in UI banner and README)**: picks top-k sentences from chunks above threshold, wraps them in a fixed template with `[chunk_id]` citations; confidence band High/Medium/Low from score margins; abstains when top score < profile threshold.
- **Threshold profiles**: `strict` / `balanced` / `exploratory` presets (k, min_score).
- **Provenance UX**: citation chips on each answer link to a chunk view with the source text highlighted; `/history` lists all past Q&A.
- **Visual-diff snapshot mode**: `scripts/snapshot.py --seed 42` loads fixture corpus, asks 3 canned questions, renders canonical HTML to `snapshots/run_<seed>.html` — byte-identical across runs with the same seed (verify via sha256sum).

## 5. Domain Workflows
**Happy path**: serve → upload sample minutes PDF → ask about a roll-call vote → get an answer with 2–4 citation chips, confidence band, and latency → click a chip → highlighted source chunk → entry persisted in history.
**Edge cases**: `.docx` → 400 with plain message; scanned PDF → distinct rejection; question with zero corpus overlap ("quantum entanglement") → abstain card, not a fabricated answer; duplicate upload → notice only; empty/punctuation-only question → validation error.

## 6. Data & Persistence
CSV files only — no SQLite, no ORM, no vector DB. Atomic-ish writes (temp file + rename). Fixture corpus in `fixtures/`: 2 `.txt` + 1 small text-based `.pdf` (each < 60 KB), authentically municipal (agenda, minutes with motions/roll-call votes, ordinance excerpt) — no lorem ipsum.

## 7. UX / API Surface
Static HTML only: server-rendered pages (Flask suggested, stdlib templates), no JS framework, no build step, minimal inline CSS. Pages: Upload, Ask, Answer detail, History, Chunk view. Stub banner on every answer: *"Stub LLM — extractive only, no generative model."*
Endpoints, documented in README with working curl examples: `POST /ingest` (multipart), `POST /ask`, `GET /history`, `GET /chunk/<chunk_id>`, `GET /healthz`. All requests logged to `request_log.csv`.

## 8. Quality, Security, Reliability
`--seed` flag (default 42) on CLI + notebook: same corpus + question + seed → identical CSV rows and identical snapshot bytes. Never crash on empty/partial files; user errors → 4xx with plain-language messages. Sanitize filenames; enforce size cap; no network calls at runtime; no secrets. Cold start shows a guided empty state with a "load sample corpus" action.

## 9. Documentation & Testing
README: quickstart (`pip install -r requirements.txt`, `python scripts/ingest.py fixtures/`, `python scripts/serve.py`), curl examples, pipeline description, **Limitations** (stub is extractive; English tokenization; scanned PDFs unsupported; lexical TF-IDF ≠ semantic search; single-user), how to swap in a real LLM, reproducibility notes. `notebooks/walkthrough.ipynb` runs top-to-bottom offline demonstrating ingest → ask → citations with the seed respected. Smoke tests only (pytest, < 10s total, no downloads): validation rejects bad files; fixture ingest yields expected chunk count; ask returns citations; abstention case; two snapshot runs produce identical bytes.

## 10. Constraints & Non-Goals
Python 3.10+. Locked: static HTML UI, CSV persistence, notebook + script delivery. No GPU/torch/transformers, no cloud APIs, no auth (single-user local tool), no JS frameworks, no model training, no multi-turn chat memory, not an MLOps platform.

## 11. Acceptance Criteria
- [ ] Valid `.txt`/`.pdf` uploads are chunked, indexed, and visible in the UI
- [ ] Unsupported/corrupt/scanned/oversize inputs rejected with distinct messages
- [ ] Duplicate upload detected; no duplicate CSV rows
- [ ] Ask returns extractive answer with ≥1 chunk citation and confidence band, or abstains below threshold
- [ ] Citation click-through shows the highlighted source chunk
- [ ] History survives server restart (reloaded from CSV)
- [ ] `snapshot.py --seed 42` run twice → identical bytes (sha256 match)
- [ ] Notebook executes top-to-bottom offline
- [ ] pytest smoke suite passes in <10s with no network
- [ ] README limitations + curl examples work as written

## 12. Uniqueness / Anti-Clone Constraints
This is not a generic "chat with your PDF" clone. Municipal-records terminology (agenda, motion, ordinance, roll-call vote, public comment) must appear in fixtures, UI copy, and schemas. Sentence-level citation provenance and the abstain-over-hallucinate policy are mandatory, rendered as citation chips — not bare markdown links. The stub LLM must be visibly labeled in the UI and README. No "upload a resume" framing, no generic chatbot shell, no placeholder-only pages.

When done, print `DONE task_4: AI document assistant` and start the next task immediately.

---

## Task 05 — Sentiment triage inbox
**workdir:** `task_ai_ml_05`
**id:** `ai_ml_05_sentiment-triage-inbox`
**seed (original):** Create a support inbox that classifies message sentiment/urgency with a small local model or lexicon baseline and routes tickets to queues.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "single_shot", "repo_state": "partial_scaffold", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "low", "language_runtime": "javascript", "artifact_type": "backend_api", "task_family": "ml_inference_eval", "business_domain": "social_comms", "ui_surface": "api_only", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "export/import round-trip as acceptance", "delivery": "static_build_preview", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PLATFORM PROMPT — Harborline Dispatch

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product Identity

Build **Harborline Dispatch**, an API-only message triage service for a fictional
regional ferry + bike-share co-op ("Harborline Transit"). Riders send messages
("the dock gate at Pier 4 is jammed and my card was charged twice") and the
service classifies **sentiment**, **urgency**, and **issue category** with a
deterministic, fully local **lexicon-scoring baseline** — no external model
calls, no downloads — then routes each ticket into an operations queue with an
SLA hint. Staff engineers are the operators: every classification must expose
*why* it fired (matched terms, score margins) and low-confidence results must
land in a human review lane, never auto-silenced.

Stack (locked): **Node.js 20+, JavaScript (ESM), SQLite** via `better-sqlite3`,
plain `node:test` for tests. No Python, no ORM, no cloud APIs.

## 2. Target Users & Jobs-to-Be-Done

- **Ops dispatcher**: needs incoming rider mail auto-sorted into named queues
  (`safety`, `fare-billing`, `fleet-damage`, `accessibility`, `general`) so
  safety incidents surface first.
- **Staff engineer (primary voice)**: needs deterministic, testable scoring,
  explainable decisions, and a portable export/import for environment parity.
- **QA analyst**: needs fixtures and an export → wipe → import round-trip to
  verify persistence integrity.

## 3. Core Entities

- **Ticket** — id, channel (`email|sms|kiosk`), author handle, subject, body,
  status (`open|triaged|review|resolved`), created_at.
- **Classification** — ticket_id, sentiment (`positive|neutral|negative` +
  score), urgency (`p1..p4` + score), category, confidence (margin between top
  and runner-up scores), evidence (array of matched lexicon terms with weights).
- **Queue** — name, description, SLA minutes, routing rule snapshot.
- **AuditLog** — every ingest, classification, re-route, export, and import
  event with timestamp + payload hash.

## 4. Major Feature Areas

- **Lexicon classifier** (`src/lexicon/`): JSON lexicons for sentiment terms,
  urgency amplifiers ("trapped", "bleeding", "deadline"), and category keywords
  mapped to Harborline queues. Must handle **negation** ("not urgent"),
  **intensifiers** ("very", "extremely"), and cap body length scanned.
- **Routing engine**: pure function `(scores, thresholds) → {queue, sla, review}`
  driven by a `config/routing.json` so thresholds are tunable without code edits.
  Confidence below threshold → `review` queue, preserving the suggested queue.
- **Ingestion API**: validates payload shape, rejects empty bodies, overlong
  messages (>4000 chars), and unknown channels with clear 4xx errors
  distinguished from 500 classifier failures.
- **Explainability**: every classification response includes `evidence[]` with
  term, weight, and which lexicon fired.
- **Export/Import**: `GET /export` streams a versioned JSON bundle (tickets,
  classifications, queues, audit log). `POST /import` validates schema version
  and restores state idempotently into a wiped or fresh database.
- **Stats**: `GET /stats` returns per-queue counts, urgency histogram, and
  review-lane backlog.

## 5. Domain Workflows

**Happy path**: POST a rider message → 201 with ticket id + inline
classification → ticket appears under `GET /queues/safety/tickets` because
"gate jammed, card charged twice" hits urgency amplifier + billing keyword;
routing prefers `safety` on ties (documented precedence).

**Edge cases**: empty body → 422 with field-level errors; sarcasm/negation
("not exactly thrilled the ferry left early") still scores negative;
confidence < threshold → status `review` with `suggested_queue`; importing a
bundle into an existing DB → 409 unless `?mode=replace`; classifier never
throws on emoji-only or non-Latin input (falls back to `general`, low
confidence, flagged for review).

## 6. Data & Persistence

Single SQLite file (`data/harborline.db`, path env-overridable). Migrations run
on boot from `migrations/001_init.sql`. Seed script inserts 8 realistic rider
fixtures spanning every queue. All writes wrapped in transactions; WAL mode on.

## 7. API Surface

`POST /tickets` · `GET /tickets` (filter by queue/status/urgency) ·
`GET /tickets/:id` · `POST /tickets/:id/reroute` (human override, audited) ·
`GET /queues/:name/tickets` · `GET /stats` · `GET /export` · `POST /import` ·
`GET /health`. JSON everywhere; errors shaped `{error, code, details}`.
No auth (single-operator MVP) — document this as a non-goal.

## 8. Quality, Security, Reliability

Parameterized queries only; body-size limit; deterministic scoring (same input
→ same output, unit-tested); classifier latency < 5ms/message locally; server
must never crash on malformed JSON.

## 9. Documentation & Testing

**README**: quickstart (`npm install && npm run seed && npm start`), curl
examples for every endpoint, lexicon authoring guide, limitations (English-only
lexicon, sarcasm blind spots, no learning loop). **Static build preview**:
`npm run preview` classifies seeded fixtures and writes `preview/index.html` —
a self-contained report of queue distribution, sample evidence, and stats that
opens without the server. **Tests** (`node --test`, must finish < 10s): lexicon
negation/intensifier cases, routing precedence + review-lane fallback,
validation rejections, ingest happy path over HTTP, and the export/import
round-trip.

## 10. Constraints & Non-Goals

No external ML APIs, no model downloads, no training. No UI beyond the static
preview artifact. No multi-tenant auth. No WebSockets/streaming. Keep total
dependencies ≤ 3 runtime packages.

## 11. Acceptance Criteria

- [ ] `POST /tickets` returns structured `{sentiment, urgency, category,
      confidence, evidence[]}` for a valid rider message
- [ ] Invalid payloads (empty body, bad channel) fail with clear 4xx, never 500
- [ ] Low-confidence classifications route to `review` with a suggested queue
- [ ] `GET /queues/safety/tickets` reflects routing precedence on fixture data
- [ ] **Export → wipe DB → import → `GET /stats` and ticket payloads are
      byte-identical to pre-export state** (round-trip test passes)
- [ ] `node --test` suite green; `npm run preview` emits `preview/index.html`
- [ ] README documents limitations and curl walkthrough

## 12. Uniqueness / Anti-Clone Constraints

This is **not** a generic sentiment demo: lexicons, queues, and fixtures must
use Harborline Transit vocabulary (piers, dock gates, fare cards, vessel names),
routing must encode the safety-over-billing precedence rule, and evidence
output must name the lexicon that fired. Do not ship placeholder lexicons
("good"/"bad" only) or a todo-app-shaped CRUD with an AI label.

When done, print `DONE task_5: Sentiment triage inbox` and start the next task immediately.

---

## Task 06 — Tabular churn predictor demo
**workdir:** `task_ai_ml_06`
**id:** `ai_ml_06_tabular-churn-predictor-demo`
**seed (original):** Build a churn prediction demo: upload CSV, train a simple sklearn model, show feature importances, and predict on new rows.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "notebook_analysis", "task_family": "data_wrangling", "business_domain": "finance_fintech", "modality": "text_code", "ui_surface": "excel_workbook", "persistence": "json_file", "testing_depth": "unit_plus_smoke", "novelty_hook": "observability: structured logs + simple metrics endpoint", "delivery": "worker_plus_api"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PLATFORM PROMPT — Holdfast Retention Workbench

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


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

When done, print `DONE task_6: Tabular churn predictor demo` and start the next task immediately.

---

## Task 07 — Embedding search for FAQs
**workdir:** `task_ai_ml_07`
**id:** `ai_ml_07_embedding-search-for-faqs`
**seed (original):** Create an FAQ semantic search API using local embeddings (or TF-IDF fallback), with admin CRUD for FAQ entries and ranked answers.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "resume_mid_task", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "medium", "value": "medium", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "ml_inference_eval", "business_domain": "general_utilities", "ui_surface": "mobile_web", "persistence": "postgres_optional", "testing_depth": "browser_smoke", "novelty_hook": "plugin/extension hook (one stub plugin)", "delivery": "monorepo_client_server", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# AnswerAtlas — On-Prem Semantic FAQ Search for Enterprise Service Desks

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product identity
**AnswerAtlas** is a Go monorepo (`/server`, `/web`, `/plugins`) delivering semantic FAQ retrieval for mid-market enterprise service desks (shared IT/HR support). All retrieval runs **locally**: a deterministic pure-Go TF-IDF + cosine scorer (with token-bigram overlap boost) sits behind a `Scorer` interface, so a real local embedding model can be swapped in later — **no model downloads, no external AI APIs during this run**. Answers are returned ranked, cited, and bucketed into governed confidence tiers. One stub ranker plugin demonstrates the extension hook. Voice: enterprise buyer — auditability, thresholds, on-prem posture, no black boxes.

## 2. Target users & jobs-to-be-done
- **Service desk operations lead (buyer):** wants defensible answer quality, per-query audit trail, and threshold policies controlling when the system auto-answers vs. escalates.
- **Knowledge curator:** maintains FAQ entries, needs duplicate detection *before* publishing.
- **Frontline employee/agent on a phone:** types a question, gets ranked cited answers in seconds.

## 3. Core requirements / entities
- `FAQEntry`: id, question, answer, category (IT / HR / Facilities), tags, status (`draft|published|archived`), source_ref (e.g. "KB-1042"), version, updated_at.
- `ThresholdProfile`: id, name, auto_answer_min, suggest_min, is_active (exactly one active).
- `QueryLog`: id, query_text, top_k results (JSON), tier, latency_ms, scorer_version, created_at.
- `FeedbackLabel`: id, query_log_id, faq_entry_id, vote (up/down), optional comment.
- `PluginRegistry`: registered ranker plugins + enabled flag.

## 4. Major feature areas
- **Retrieval engine:** tokenize/normalize → TF-IDF vectors → cosine similarity + bigram overlap bonus; top-k with float scores; fully deterministic for fixtures.
- **Confidence tiers:** `auto-answer` (score ≥ auto_answer_min), `suggestions` (≥ suggest_min), `escalate` (below — returns handoff card with category routing hint). Distinct visual treatment per tier.
- **Admin console:** full CRUD, status transitions, and a **duplicate-compare panel**: on create/edit, show top-3 most similar existing entries side-by-side (question + score) with a "publish anyway" confirm.
- **Plugin hook:** `RankerPlugin` interface (`Name()`, `Rescore(query string, results []ScoredResult) []ScoredResult`); ship one stub, `RecencyBoost`, that nudges scores by entry `updated_at`. Toggleable via API; when disabled, results equal baseline ranking exactly.
- **Feedback + review queue:** thumbs up/down per result; admin sees a queue of downvoted (entry, query) pairs.
- **Audit:** every search logged with tier and latency; browsable read-only list.

## 5. Domain workflows
**Happy path:** first run seeds ≥12 authentic IT/HR service-desk FAQs → user searches "vpn keeps dropping on wifi" → ranked cited answers with score bars, matched-term highlighting, tier badge → user leaves feedback → curator reviews downvotes, edits entry, sees duplicate warning, publishes.
**Edge cases:** empty corpus → "no published entries" state; gibberish query → escalate card (never a fake answer); query >500 chars or empty → 400 with field error; drafts/archived excluded from search; plugin disabled mid-session → next request uses baseline; duplicate submission flagged but allowed with confirm.

## 6. Data & persistence
Repository interface with two implementations: (a) default in-memory store + JSON snapshot (`data/seed_faqs.json`, loaded on boot, writes appended), (b) Postgres via `DATABASE_URL` with SQL migrations in `/server/migrations`. **Postgres is strictly optional — the app must boot and pass all tests with zero external services.**

## 7. UX / API surface
Mobile-first web client (vanilla JS served by the Go server from `/web`): `/` search page, `/admin` console. Loading spinner during search; validation errors (400) visually distinct from engine failures (500). Endpoints:
- `POST /api/search` `{query, top_k}` → `{tier, results:[{entry_id, question, snippet, score, matched_terms, source_ref}]}`
- `GET/POST/PUT/DELETE /api/admin/faqs` (bearer `ADMIN_TOKEN` env var)
- `GET/PUT /api/admin/profiles`, `GET /api/admin/review`, `GET /api/audit`
- `POST /api/feedback`
- `GET /api/plugins`, `POST /api/plugins/{name}/toggle`
Search is unauthenticated (internal tool); admin routes require the token.

## 8. Quality, security, reliability
Validate all inputs; never crash on empty/partial data; 2s handler timeout; scores clamped [0,1]; audit log is append-only; admin token never logged; deterministic scoring so CI fixtures are stable.

## 9. Documentation & testing
README: architecture, run instructions, curl examples for every endpoint, threshold-profile tuning guide, plugin-authoring snippet, and "enabling real embeddings later" notes + limitations (English-only tokenization, no synonym expansion, TF-IDF semantic limits). Tests: Go unit/handler tests for search happy path, tier assignment, validation failures, duplicate-compare, plugin on/off equivalence. `scripts/smoke.sh`: boots server, GET `/` (asserts search UI + domain copy present), POSTs a fixture search, asserts tier + ranked JSON — the browser-smoke gate.

## 10. Constraints & non-goals
No LLM calls, no vector DB, no network fetches of models/weights, no multi-tenant SaaS, no retraining. Not a chatbot — responses are retrieval with citations, never generated prose.

## 11. Acceptance criteria
- [ ] `go run ./server` boots with no external services; seeded corpus searchable
- [ ] Valid query returns ranked results with scores, matched terms, tier badge
- [ ] Empty/oversized query → clear 400; gibberish → escalate card
- [ ] Admin CRUD works with token; duplicate-compare panel appears on similar entry
- [ ] Threshold profile edit changes tier boundaries on next search
- [ ] RecencyBoost stub plugin toggles and measurably reorders vs. baseline
- [ ] Feedback lands in review queue; searches appear in audit log with latency
- [ ] Go tests + `scripts/smoke.sh` pass; README curl examples succeed

## 12. Uniqueness / anti-clone constraints
Use service-desk vocabulary throughout (confidence tier, escalation, curator, threshold profile, source_ref) — not generic "search app" copy. No todo-list UI, no lorem ipsum, no placeholder cards; seed FAQs must be realistic ("MFA prompt fatigue lockout", "expense report per-diem caps"). The plugin must genuinely rescore results, not be a no-op label. Forbidden: ChatGPT-wrapper framing, embedding downloads at runtime, or a desktop-only layout — the client must be usable on a 375px viewport.

When done, print `DONE task_7: Embedding search for FAQs` and start the next task immediately.

---

## Task 08 — OCR receipt field extractor
**workdir:** `task_ai_ml_08`
**id:** `ai_ml_08_ocr-receipt-field-extractor`
**seed (original):** Build a receipt field extractor: accept images, stub OCR to text if needed, parse merchant/date/total with rules, and return structured JSON + UI review.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "ml_inference_eval", "business_domain": "finance_fintech", "modality": "text_code", "ui_surface": "static_html", "persistence": "memory_only", "testing_depth": "smoke_only", "novelty_hook": "multi-theme or multi-difficulty presets", "delivery": "library_plus_demo_app"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PLATFORM PROMPT — SlipSift

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product identity
Build **SlipSift**, a Python library + demo web app that extracts structured fields (merchant, date, total, currency) from receipt images and presents them in a review dashboard with spending charts. OCR is **stubbed** (no heavy ML deps): a deterministic fake-OCR layer maps uploads to a small corpus of canned receipt texts, and users may also paste raw receipt text directly. The parsing engine is rule-based (regex + heuristics) and is the real product. The pitch: "a solo dev's pocket bookkeeper — snap, parse, confirm, see where the money went."

## 2. Target users & primary jobs-to-be-done
- **Primary persona:** a solo developer / freelancer who hoards paper receipts and wants quick totals per merchant and per day without a SaaS subscription.
- Jobs: (a) turn a receipt photo into trustworthy structured data fast; (b) eyeball and fix the extraction before trusting it; (c) see simple spending patterns at a glance; (d) reuse the parser as a library in their own scripts.

## 3. Core requirements / entities (all in-memory)
- **ReceiptSubmission**: id, original filename, OCR source (`stub` | `paste`), raw text, submitted-at timestamp.
- **ExtractionResult**: merchant, date (ISO), total (float), currency, per-field confidence (0–1), preset used, list of flagged issues (e.g., `"total not found"`, `"ambiguous date"`).
- **ReviewRecord**: links submission → result, plus user-confirmed/edited fields and status (`pending` | `confirmed`).
- No database, no auth, no users table. Everything lives in module-level Python lists/dicts and resets on restart — state this clearly in the UI footer and README.

## 4. Major feature areas
- **Library core (`slipsift` package):** `extract(text: str, preset: str = "us_corner_store") -> dict` exposing merchant/date/total/currency + confidences; importable without the web app.
- **Rule engine:** merchant = first plausible non-noise line (skip lines like `***`, card tails); date regexes for `MM/DD/YYYY`, `DD.MM.YYYY`, `Mar 4 2025`, ISO; total = amount near keywords `TOTAL`, `AMOUNT DUE`, `GRAND TOTAL` (prefer last/highest); currency inferred from symbol or preset default. Confidence degrades per missing cue.
- **Extraction presets (the multi-difficulty novelty — required):** at least three shipped profiles that *measurably change parsing behavior*:
  - `us_corner_store` — USD default, MDY date preference, lenient.
  - `eu_bistro` — EUR default, DMY preference, handles comma decimals (`12,40`).
  - `strict_audit` — any currency, caps confidence at 0.4 unless an explicit TOTAL keyword AND a parseable date are found.
- **Stub OCR layer:** deterministic mapping (e.g., hash of file bytes) to one of ≥5 bundled sample receipt texts (US grocery, EU café with comma decimals, ambiguous-date fuel receipt, faded/partial receipt missing total, itemized restaurant). Clearly labeled `OCR STUB` in code and UI; README documents how to swap in `pytesseract` later.
- **Review queue UI:** pending extractions with editable fields and per-field confidence badges; confirm saves the corrected record.
- **Dashboard charts:** server-rendered (inline SVG is fine — no JS build step): spend by merchant (bar), spend by date (bar/line), extraction confidence per receipt (color-coded). Charts reflect **confirmed** receipts only.

## 5. Domain-specific workflows
- **Happy path:** open app → click a bundled sample or upload a PNG/JPG → stub OCR yields text → extraction runs under a chosen preset → review card shows fields + confidences → user fixes the date, confirms → dashboard charts update.
- **Paste mode:** textarea submission bypasses OCR entirely (also the test-friendly path).
- **Edge cases:** non-image/oversize upload → clear 400 with supported formats listed; receipt with no TOTAL → result still returned, total `null`, issue flagged, confidence low; ambiguous `03/04/2025` → resolved by preset preference, issue `"ambiguous date: assumed MDY"` recorded; empty/garbage text → all-null result with zero confidence, no crash.

## 6. Data & persistence expectations
Memory-only: a simple `store.py` (lists + dicts) is enough. Confirmed edits mutate the in-memory record. No files written except optional upload temp handling. README must state data vanishes on restart and that swapping in SQLite is a documented one-paragraph future step.

## 7. UX / API surface expectations
- Single-page-ish Flask app (or equivalent micro-framework), `render_template_string` acceptable to keep file count low. Pages/sections: submit (upload + paste + preset selector), review queue, dashboard.
- JSON API mirroring the UI:
  - `POST /api/extract` — multipart image **or** JSON `{"text": ..., "preset": ...}` → ExtractionResult JSON.
  - `GET /api/receipts` — all records with status.
  - `POST /api/receipts/<id>/confirm` — accepts corrected fields.
  - `GET /api/stats` — aggregates backing the charts.
- Loading state during "OCR" (a brief artificial delay is fine), distinct error rendering for validation failures vs parse failures.

## 8. Quality, security, and reliability expectations
Validate extension + size (≤2 MB) on upload; never trust pasted text length (cap ~10k chars); all parsing is pure-Python regex (no eval, no subprocess); parser must never raise on malformed input — return a low-confidence result with issues instead. Keep total deps to Flask + pytest (stdlib-only parsing; no PIL/torch/tesseract required to run).

## 9. Documentation & testing expectations
- **README:** product blurb, `pip install -r requirements.txt`, `python app.py`, library usage snippet (`from slipsift import extract`), curl example for `/api/extract`, preset comparison table, OCR-swap instructions, limitations (stubbed OCR, English-ish receipts, in-memory loss, rule fragility).
- **Smoke tests only:** one small test file — parser happy path on 2 canned receipts (including the comma-decimal one), one API test posting pasted text and asserting the JSON schema, one invalid-upload rejection test. All deterministic, all offline, run in <5 s.

## 10. Constraints & non-goals
No real OCR models, no image preprocessing, no line-item extraction, no multi-currency conversion, no auth, no database, no export formats beyond the JSON API. Do not add features beyond this list; polish the listed ones instead.

## 11. Acceptance criteria
- [ ] `from slipsift import extract; extract(SAMPLE, preset="eu_bistro")` returns merchant/date/total/currency + confidences.
- [ ] App runs with `python app.py`; upload, paste, review-confirm, and dashboard all work end-to-end.
- [ ] All ≥3 presets demonstrably alter at least one extraction on the bundled samples (shown in README table or test).
- [ ] Missing-total and ambiguous-date receipts surface flagged issues, not crashes.
- [ ] Charts render confirmed data and update after a confirm.
- [ ] `pytest` smoke suite passes offline in seconds.
- [ ] README limitations + OCR-stub disclosure present.

## 12. Uniqueness / anti-clone constraints
This is not a generic CRUD or todo app: no task lists, no "items", no placeholder lorem-ipsum UI. Use receipt-domain vocabulary throughout (merchant, tender, grand total, VAT line, review queue, extraction profile). Presets must be functional parsing profiles, not cosmetic renames. The dashboard must show receipt-spend charts specifically, not a generic counter widget. Ship few files, real behavior, zero dead buttons.

When done, print `DONE task_8: OCR receipt field extractor` and start the next task immediately.

---

## Task 09 — Toxicity filter microservice
**workdir:** `task_ai_ml_09`
**id:** `ai_ml_09_toxicity-filter-microservice`
**seed (original):** Implement a toxicity/profanity filter microservice with batch and streaming endpoints, allowlists, and unit tests on fixtures.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "approval_gated", "repo_state": "partial_scaffold", "tool_profile": "mixed", "user_persona": "staff_eng", "complexity": "hard", "value": "hard", "language_runtime": "rust", "artifact_type": "backend_api", "task_family": "ml_inference_eval", "business_domain": "security_privacy", "ui_surface": "game_loop_window", "persistence": "sqlite", "testing_depth": "unit_plus_smoke", "novelty_hook": "chaos toggle: inject one recoverable failure path", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# Sluicegate — Lexical Moderation Gate with Live Ops Window

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product Identity

Build **Sluicegate**, a deterministic toxicity/profanity screening service for real-time chat platforms (game lobbies, livestream chat, community forums). It exposes batch and streaming HTTP endpoints, persists every verdict to SQLite, and ships with a **native game-loop window** — a 60fps "moderation ops console" that renders verdicts as a live severity-colored ticker with rate sparklines.

**Stack (locked):** Rust (stable), `axum` + `tokio` for HTTP/SSE, `rusqlite` (bundled SQLite) for persistence, `macroquad` for the game-loop window. No ML model downloads — detection is a documented, deterministic normalization + lexicon pipeline (see §4). One command must boot everything: `cargo run --release` (or `./dev.sh`) starts API on `:8080` and opens the window; `--headless` runs API-only for CI.

**Persona voice:** this PRD is written by a staff engineer — expect explicit tradeoffs, failure semantics, and checkable acceptance.

## 2. Target Users & Jobs-to-be-Done

- **Trust-and-safety integrator**: embed a screening call before persisting chat messages; needs sub-10ms local verdicts and structured evidence.
- **Community moderator**: watch the live window during an event; needs severity-tiered visibility, not a boolean.
- **Ops engineer**: needs auditability (every verdict persisted) and a chaos drill path to prove the write pipeline survives DB faults.

## 3. Core Entities

- `LexiconTerm { term, category, severity_tier (T1 profanity / T2 harassment / T3 slur-threat), locale }` — seeded from a vendored JSON file, versioned.
- `AllowlistEntry { scope (tenant/channel), pattern, is_prefix }` — overrides lexicon matches (e.g., a medical channel allows anatomical terms).
- `ScreenVerdict { id, tenant, input_hash, action, score, tier_max, evidence_json, latency_us, created_at }` — append-only audit record.
- `ChaosState { enabled, drop_rate }` — runtime-toggleable, single row.

## 4. Major Feature Areas

**Normalization + matching pipeline (the "model"):**
1. Unicode case-fold, strip zero-width/diacritic characters, collapse repeated chars (`loooool` → `lool`→`lol`), map a small vendored leetspeak/homoglyph table (`4→a`, `0→o`, `@→a`).
2. Tokenize; match lexicon terms as whole tokens first, then substring matches on normalized tokens.
3. Score: `tier_weight × match_confidence` where confidence = 1.0 exact token, 0.8 normalized, 0.6 substring. Map score to `ALLOW / REVIEW / BLOCK` via configurable thresholds (env or config file).
4. Output schema: `{ action, score, tier_max, evidence: [{ span: [start,end], matched, term_category, confidence, overridden_by_allowlist }] }` — top-k evidence spans, byte offsets into the *original* input.

**Endpoints:**
- `POST /v1/screen` — single text → verdict JSON.
- `POST /v1/screen:batch` — JSON array → array of verdicts, per-item error isolation.
- `POST /v1/screen:stream` — NDJSON lines in, NDJSON verdicts out, flushed per line (chat-replay simulation).
- `GET /v1/events` — SSE broadcast of every verdict (feeds the window).
- `GET/POST/DELETE /v1/allowlist` — scoped allowlist management.
- `GET /v1/health` — includes `pending_writes` and `chaos` state.
- `POST /v1/chaos {enabled, drop_rate}` — runtime chaos toggle.

**Chaos toggle (recoverable failure path — required novelty):** when enabled (flag `--chaos`, endpoint, or pressing `C` in the window), SQLite writes randomly fail at `drop_rate` (default 0.25) via an injected error in the persistence layer. Verdicts must **still be returned to callers**; failed writes go to an in-memory retry buffer drained with backoff. `pending_writes` exposes buffer depth; the window shows a red "CHAOS — buffering N writes" banner. Disabling chaos drains the buffer to zero with **no verdict loss and no crash**.

**Game-loop window (macroquad, 60fps):** scrolling verdict ticker (severity-colored chips: green/yellow/red), verdicts/sec sparkline, ALLOW/REVIEW/BLOCK counters, chaos banner, keybindings `C` toggle chaos, `Space` pause feed. Connects via SSE; `--headless` skips it entirely.

## 5. Domain Workflows

**Happy path:** client POSTs a chat message → normalize → lexicon match → allowlist check (matching entries mark evidence `overridden`, suppressing the action) → score → persist verdict → return JSON → SSE emits → window ticks.

**Edge cases that must behave:** empty string (400 with code `EMPTY_INPUT`); input > 8KB (413); invalid UTF-8 (422); unknown tenant scope on allowlist write (400); batch with one corrupt item (that item errors, others succeed); lexicon file missing at boot (refuse to start with a clear message); 50 rapid chaos toggles (no deadlock, buffer drains).

## 6. Data & Persistence

SQLite at `./sluicegate.db` (path via env). Schema created by embedded migrations on boot — idempotent. Verdicts are append-only, indexed on `created_at` and `action`. Lexicon + allowlist seed data versioned (`schema_version` table). No external DB, no network fetches at runtime.

## 7. UX / API Surface

- README documents every endpoint with runnable `curl` examples that must actually succeed against a fresh boot.
- Errors are structured: `{ error: { code, message } }` with correct status codes; validation failures (4xx) are distinguishable from internal failures (5xx).
- First-run: `dev.sh` optionally seeds a sample tenant and prints three ready-to-paste curls (clean, T1, T3).

## 8. Quality, Security, Reliability

- Input size caps; no panics on malformed input — every handler returns structured errors.
- `action` thresholds configurable without recompile (TOML config + env overrides).
- Concurrent requests safe: SQLite behind a connection pool or serialized writer; chaos buffer bounded (shed with explicit 503 + `Retry-After` past 10k pending).

## 9. Documentation & Testing

**Tests (must pass with `cargo test`):**
- Unit tests on a **fixture corpus** (`fixtures/cases.json`): ≥25 labeled cases covering exact/normalized/substring matches, leetspeak evasion (`f4gg0t`-style obfuscation of fixture terms — keep fixtures synthetic, e.g., invented slur-like tokens like `gronk`/`zibble` mapped to T3 to avoid shipping real slurs in the repo), allowlist override, empty input, unicode zero-width injection.
- Unit test: chaos injection at drop_rate 1.0 → all writes buffered → disable → drained, all rows present.
- Smoke test (`scripts/smoke.sh`): boots headless on a random port, curls screen/batch/stream/health/chaos round-trip, asserts JSON shape, exits non-zero on failure. Must complete in <30s and **not** require a display.

**README:** architecture sketch, normalization stages, how to extend the lexicon, limitations section (deterministic pipeline = no semantic/context understanding; English-biased lexicon; evasion arms race; fixture tokens are synthetic).

## 10. Constraints & Non-Goals

- No ML model downloads, no GPU, no network calls at runtime.
- Not a full moderation dashboard (no auth, single-process, no user accounts).
- No real slur lists committed — synthetic fixture terms only, with a documented path to import a real lexicon.
- Window must not be required for the service to function.

## 11. Acceptance Criteria

- [ ] `./dev.sh` or `cargo run` boots API + window with one command; `--headless` boots API only.
- [ ] `POST /v1/screen` returns the full schema (action, score, tier_max, evidence spans with byte offsets).
- [ ] Batch endpoint isolates per-item errors; stream endpoint flushes NDJSON per line.
- [ ] Allowlist POST → subsequent matching input returns `ALLOW` with `overridden: true` evidence.
- [ ] Chaos on at 1.0 drop rate: `/v1/health` shows `pending_writes > 0`; chaos off: drains to 0; row count in SQLite equals total screened.
- [ ] Every verdict (including chaos-buffered ones) is queryable in SQLite.
- [ ] `cargo test` passes (fixtures + chaos recovery); `scripts/smoke.sh` passes headlessly.
- [ ] README curl examples succeed verbatim against a fresh boot.
- [ ] Window renders live verdicts with severity colors and chaos banner; `C` toggles chaos end-to-end.

## 12. Uniqueness / Anti-Clone Constraints

- Not a boolean "is_bad" toy: severity tiers, evidence spans, confidence, and allowlist override semantics are mandatory.
- No placeholder UI: the window must render real streamed verdicts, not static text.
- Use domain-authentic vocabulary throughout (verdict, tier, evidence span, tenant scope) — no "todo", no "item", no lorem ipsum.
- Synthetic lexicon tokens only (`gronk`, `zibble`, etc.) — this is both a safety constraint and a fingerprint for this run.

When done, print `DONE task_9: Toxicity filter microservice` and start the next task immediately.

---

## Task 10 — Time-series anomaly flagger
**workdir:** `task_ai_ml_10`
**id:** `ai_ml_10_time-series-anomaly-flagger`
**seed (original):** Create a time-series anomaly flagger: ingest metric CSV, detect spikes with z-score/IQR, plot anomalies, and export flagged windows.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "single_shot", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "low", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "data_visualization", "business_domain": "devops_platform", "ui_surface": "cli_tui", "persistence": "json_file", "testing_depth": "smoke_only", "novelty_hook": "domain twist: niche audience + unusual constraint", "delivery": "single_readme_run", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# Project Request: HivePulse — Offline Anomaly Flagger for Backyard Beekeepers

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


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

When done, print `DONE task_10: Time-series anomaly flagger` and start the next task immediately.

---
