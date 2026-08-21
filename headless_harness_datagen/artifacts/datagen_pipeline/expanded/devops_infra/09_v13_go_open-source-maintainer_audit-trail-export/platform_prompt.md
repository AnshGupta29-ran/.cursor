# VARIANT v13_go_open-source-maintainer_audit-trail-export - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `go`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `audit_trail_export`
- **ui_surface**: `desktop_window`
- **persistence**: `csv_files`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `go`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v13_go_open-source-maintainer_audit-trail-export`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v13_go_open-source-maintainer_audit-trail-export` when demoable.

---

## BASE PRD (honor unless mutated above)

# PROJECT OBJECTIVE — Holdfast: Backup Job Orchestration Control Plane

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `go`
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
**Holdfast** is a single-binary, API-only backup job orchestrator for small platform teams. It schedules filesystem backup jobs against sandboxed local destinations, enforces retention policies, and produces **restore dry-run reports** so operators gain restore confidence without touching production data. Voice: a staff engineer built this for on-call humans — terse, deterministic, auditable. No UI; the JSON API *is* the product.

## 2. Target users & jobs-to-be-done
- Solo platform/staff engineer running homelab or small-fleet backups: "prove my backups are restorable before I need them."
- SRE auditing retention posture: "show me exactly what pruning would delete before it runs."
- Operator migrating control-plane state between hosts: "export everything, import on the new box, get byte-identical state back."

## 3. Core entities (SQLite-backed)
- **Destination**: id, name, type (`local-dir` only), base_path (must resolve under configured `--data-root`), created_at.
- **BackupJob**: id, name, source_path, destination_id, schedule (`interval` e.g. `6h`, min `1m`), retention (`keep_last` N ≥ 1 and/or `max_age_days`), enabled, next_run_at.
- **Run**: id, job_id, status (`running|success|failed`), started/finished_at, file_count, byte_count, manifest_path, error.
- **Manifest** (per run, JSON file at destination): entries of {path, size, sha256}.
- **RestoreReport** (dry-run): id, run_id, generated_at, files_listed, bytes, missing_on_destination, planned_steps[], would_overwrite[].
- **AuditEntry**: id, ts, action, entity, entity_id, detail (actor always `local-trusted`).

## 4. Major feature areas
- **Executor**: `POST /v1/jobs/{id}/run` synchronously copies source files into `<dest>/<job>/<run_id>/` + writes manifest.json with real SHA-256s. One active run per job (409 on overlap).
- **Scheduler**: background ticker fires due enabled jobs; next-fire computed by a pure `NextFire(now, schedule)` function (unit-tested).
- **Retention**: `POST /v1/retention/preview` (dry list of prune candidates) and `POST /v1/jobs/{id}/prune?confirm=true` (deletes run rows + artifact dirs; refuses without confirm).
- **Restore dry-run**: `POST /v1/runs/{id}/restore-dry-run` validates manifest entries against destination bytes and emits a persisted report; never writes to any source path.
- **Export/Import (headline feature)**: `GET /v1/export` streams a versioned envelope `{"format":"holdfast/v1","exported_at":..., "destinations":[...],"jobs":[...],"runs":[...],"reports":[...]}`. `POST /v1/import?mode=replace|merge` validates format, is idempotent (stable IDs, re-import yields zero duplicates), and is fully audited. **Round-trip invariant: export → import into empty DB → export again must be deep-equal** (ignore exported_at).
- **Audit**: every mutating endpoint writes an AuditEntry; `GET /v1/audit` lists them.

## 5. Workflows
**Happy path**: create destination → create job (schedule + retention) → trigger run → fetch run + manifest summary → generate restore dry-run report → preview retention → prune with confirm → export → reset DB → import → re-export → `diff` clean.
**Edge cases**: destination path escaping data-root (reject 400); schedule interval < 1m (reject); prune without confirm (400); dry-run against run whose artifacts were deleted (report flags missing, not 500); import with wrong `format` (422); concurrent run request (409); job with missing source_path (run fails, status recorded, API stays healthy).

## 6. Data & persistence
SQLite via pure-Go driver (`modernc.org/sqlite`, `CGO_ENABLED=0`). Migrations run at boot. Runs/reports cascade-delete with their job. Config via flags/env: `--addr` (default `127.0.0.1:8471`), `--db`, `--data-root`.

## 7. API surface expectations
REST/JSON under `/v1`, consistent error envelope `{"error":{"code","message"}}`, `GET /v1/healthz`. **Trusted-local mode** (no auth) is the documented default; optional `HOLDFAST_TOKEN` enables bearer auth. All list endpoints support `?status=` / `?job_id=` filtering.

## 8. Quality, security, reliability
Path-traversal guard on all filesystem inputs; no shelling out; server must survive a failed run without wedging; 10s per-request timeout; structured logs to stderr.

## 9. Docs & testing
README: build (`make build` → single static binary), quickstart journey with curl, safety notes. `scripts/smoke.sh` runs the full happy path and asserts the export/import diff. Light unit tests: `NextFire`, retention selection, dry-run report from fixture manifest, export/import round-trip deep-equality, 2–3 handler validation tests via `httptest`.

## 10. Constraints & non-goals
No UI, no cloud destinations, no encryption, no real restores (dry-run only), no multi-node scheduling, no third-party cron lib (stdlib only).

## 11. Acceptance criteria
- [ ] All entities persist in SQLite; server boots clean on empty DB
- [ ] Run executes real copies + SHA-256 manifest; overlap rejected with 409
- [ ] Retention preview ≠ prune; prune requires `confirm=true`
- [ ] Restore dry-run report detects missing destination artifacts
- [ ] Export → wipe → import → export round-trips deep-equal; re-import idempotent
- [ ] `go test ./...` passes; `make build` emits static binary; `scripts/smoke.sh` exits 0

## 12. Uniqueness / anti-clone rules
Use domain-authentic vocabulary (retention window, prune, manifest, restore point, dry-run) throughout code and docs. No CRUD-toy shapes, no placeholder endpoints, no generic "todo" scaffolding. The versioned `holdfast/v1` export envelope and its byte-stable round-trip are the signature behaviors and must be genuinely implemented, not stubbed.
