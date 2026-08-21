# VARIANT v04_typescript_security-auditor_audit-trail-export - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `typescript`
- **user_persona**: `security_auditor`
- **novelty_hook**: `audit_trail_export`
- **ui_surface**: `api_only`
- **persistence**: `localstorage`
- **complexity**: `hard`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `typescript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v04_typescript_security-auditor_audit-trail-export`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v04_typescript_security-auditor_audit-trail-export` when demoable.

---

## BASE PRD (honor unless mutated above)

# ShardedKeyValue — Sharded key-value store

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `typescript`
- **ui_surface:** `api_only`
- **persistence:** `sqlite`
- **complexity:** `medium`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.


## 1. Product identity
Build **ShardedKeyValue** for category `distributed_systems`. Seed intent (honor this product, do not genericize away):

> Create a sharded key-value store demo with consistent hashing, get/put, and rebalance command.

Artifact type: `backend_api`. Novelty hook: export/import round-trip as acceptance. Delivery: `static_build_preview`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`sqlite`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **medium**:
- Core entities + main workflows from the seed
- Light tests or smoke as locked by testing_depth
- Clean readable UI; charts only if ui_surface implies them

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`sqlite` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`api_only`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (medium fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`unit_light` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `unit_light` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **medium** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.
