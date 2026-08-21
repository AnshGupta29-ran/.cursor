# VARIANT v33_typescript_open-source-maintainer_dark-ops-console - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `typescript`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `dark_ops_console`
- **ui_surface**: `static_html`
- **persistence**: `csv_files`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `typescript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v33_typescript_open-source-maintainer_dark-ops-console`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v33_typescript_open-source-maintainer_dark-ops-console` when demoable.

---

## BASE PRD (honor unless mutated above)

# PLATFORM PROMPT — FlagSheet

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `typescript`
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
Build **FlagSheet**, a feature-flag admin console for non-technical product managers who think in spreadsheets. Instead of a typical developer dashboard, the entire UI is an **Excel-style workbook**: each concern (flags, targeting rules, rollout ramps, audit history, metrics) is a worksheet tab with an editable grid, a formula-bar detail strip, and a status bar. Under the hood it is a real control plane: flags have percentage rollouts with deterministic user bucketing, attribute-based targeting rules, scheduled auto-ramping, and a complete audit ledger. Architecture is **TypeScript end-to-end**, split into an **API + web server** process and a **background worker** process, persisting everything to a **single JSON file**. Observability is first-class: structured JSON logs from both processes and a simple `/metrics` endpoint.

Positioning line for the README: *"Feature rollouts you can run like a spreadsheet — no engineer required."*

## 2. Target users & primary jobs-to-be-done
- **Primary: a non-technical PM** ("Priya") who wants to ship a feature to 5% of users, ramp it safely, and prove later who changed what — without reading YAML.
- Secondary: an engineer checking evaluation behavior via API.
Jobs: (1) create a flag with variants, (2) target segments by attribute, (3) set and schedule percentage rollouts, (4) test "what would user X get?", (5) review the audit trail, (6) watch exposure counts and system health.

## 3. Core requirements / entities
Persist all in one JSON document (`data/flagsheet.json`, schema-versioned):
- **Flag**: key (slug, unique), name, description, owner, tags, enabled (bool), variants (string[], first is "off" default), rolloutPercent (0–100 int toward variants[1]), createdAt/updatedAt.
- **TargetingRule**: id, flagKey, priority (int, unique per flag), attribute (`plan` | `country` | `emailDomain` | `userId`), operator (`equals` | `in` | `contains`), value, effect (`forceVariant` + variant, or `forcePercent` + int).
- **RampPlan**: id, flagKey, steps `[{percent, soakMinutes}]`, status (`scheduled|running|paused|completed|halted`), currentStep, startedAt.
- **AuditEvent**: id, ts, actor, action (`flag.create|flag.update|flag.toggle|flag.delete|rollout.set|rule.*|ramp.start|ramp.step|ramp.halt`), flagKey, summary (human sentence), before/after diff snippet, note.
- **ExposureStat**: flagKey, variant, windowMinute, count (written by worker).

## 4. Major feature areas
- **Workbook UI** (browser, served by API): sheet tabs `Flags · Rules · Ramp Plans · Test Drive · Audit Ledger · Metrics`; grid with click-to-select, double-click/Enter inline edit, Esc cancel, Tab advance; invalid cells get red fill with tooltip; locked/computed cells visually distinct; formula-bar strip shows selected row as readable JSON; bottom status bar shows `Saved ✓ <time> · Worker: running|stopped · File: data/flagsheet.json`.
- **Flags sheet**: inline edit name/desc/percent; toggle via checkbox cell; row status chip (green=on, gray=off, amber pulsing=ramping); delete requires typing the flag key.
- **Rules sheet**: per-flag rule rows with priority ordering, operator dropdown, validation (no duplicate priority per flag).
- **Ramp Plans**: create a step list (e.g. `5%×30m → 25%×60m → 100%`), start/halt; worker advances steps after soak time and writes `ramp.step` audit events automatically.
- **Test Drive**: enter a user context (userId, plan, country, emailDomain), pick a flag, see evaluated variant + which rule matched + bucket number.
- **Audit Ledger**: read-only, monospace, newest-first, filter by flag; every mutation (human or worker) appears here.
- **Metrics sheet + `/metrics`**: JSON or Prometheus-style text exposing `flag_evaluations_total`, `ramp_steps_completed_total`, `audit_events_total`, `worker_ticks_total`, `api_requests_total`, plus per-flag exposure counts.
- **Worker process**: tick loop (configurable, default 2s) that (a) advances due ramp steps via the same store module, (b) simulates realistic traffic by evaluating all enabled flags against a deterministic pool of ~50 synthetic users and recording ExposureStats, (c) emits structured logs.
- **Evaluation API**: `POST /api/evaluate {flagKey, user}` → variant, matchedRule, bucket. Bucketing: hash of `flagKey:userId` → 0–99, in-rollout if `< percent`; rules checked in priority order, first match wins; deterministic and pure (unit-testable).

## 5. Workflows (happy path + edge cases)
Happy path: create flag `new-checkout` with variants `off/variant-a` → add rule "plan equals pro → force variant-a" → set rollout 10% → Test Drive shows pro user always gets variant-a, others bucketed → create ramp plan → watch worker bump percent and audit each step → Metrics shows rising exposures.
Edge cases that must be handled gracefully: percent outside 0–100 (reject, cell goes red); lowering a percent warns "some users may lose access — confirm"; deleting a flag with an active ramp requires halting it first; corrupt/missing JSON at boot → seed a demo dataset on first run, but on corruption refuse to start with a clear error and do not clobber the file; worker and API writing concurrently → funnel all persistence through one shared store module with atomic write (temp file + rename), last-write-wins documented.

## 6. Data & persistence
Single JSON file, atomic writes, schema `version` field, demo seed data (3 flags, 2 rules, 1 completed ramp, ~10 audit rows) generated on first launch. No external DB. README documents the file shape.

## 7. UX / API surface
REST-ish JSON: `GET/POST /api/flags`, `PATCH/DELETE /api/flags/:key`, `POST /api/flags/:key/toggle`, `PUT /api/flags/:key/rollout`, `GET/POST/DELETE /api/flags/:key/rules`, `POST /api/flags/:key/ramp`, `POST /api/ramps/:id/halt`, `GET /api/audit`, `POST /api/evaluate`, `GET /metrics`, `GET /health`. Errors return `{error, message}` with PM-readable messages. UI polls for refresh (no websockets). Trusted-local mode: no login by default; if env `FLAGSHEET_TOKEN` is set, mutating calls require header `x-flagsheet-token`. State this in README.

## 8. Quality, security, reliability
Structured JSON logs (`{ts, level, component: api|worker, msg, ...ctx}`) from both processes; one failing evaluation or a stopped worker must not freeze the UI (status bar reflects worker heartbeat); API request timeout ≤5s; never execute shell commands from user input.

## 9. Documentation & testing
README: prerequisites (Node 20+), `npm install`, `npm run dev:api`, `npm run dev:worker`, open URL, 5-minute demo script (create → rule → 10% → ramp → audit → curl /metrics), safety notes, JSON schema. **Unit tests**: bucketing determinism (same input → same bucket across runs), rule precedence, percent validation, ramp step advancement, audit emission, store round-trip + corruption rejection. **Smoke test** (`npm run smoke`): boots API on a test port with a temp data file, then asserts health → create flag → set rollout → evaluate → toggle → audit entry exists → metrics counters incremented; non-zero exit on failure. All tests and smoke must pass at runtime.

## 10. Constraints & non-goals
TypeScript only; JSON-file persistence only; workbook is a **UI metaphor** — no .xlsx import/export. Not: an SDK ecosystem, SSO/RBAC, multi-environment sync, remote config, or a LaunchDarkly clone.

## 11. Acceptance criteria
- [ ] Both processes start with documented commands; UI loads with ≥4 working sheet tabs and inline cell editing
- [ ] Create/edit/toggle/delete flag flows work; delete requires typed confirmation
- [ ] Percentage rollout + at least two rule operators evaluate deterministically via Test Drive and `/api/evaluate`
- [ ] Worker advances a scheduled ramp and each step appears in the Audit Ledger
- [ ] Every mutation (human or worker) produces an audit entry with before/after
- [ ] `/metrics` returns counters that change after activity; both processes emit structured JSON logs
- [ ] Corrupt data file → clean startup failure, file untouched
- [ ] Unit tests + smoke script pass

## 12. Uniqueness / anti-clone constraints
Must not degrade into a generic CRUD table app: the Excel-workbook metaphor (tabs, editable grid, formula bar, status bar) is mandatory, copy speaks to a non-technical PM in plain language, the worker genuinely advances ramps and simulates exposure traffic, and observability (structured logs + metrics endpoint) is built in, not bolted on. No placeholder screens, no lorem ipsum, no "Todo"-style leftovers.
