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
