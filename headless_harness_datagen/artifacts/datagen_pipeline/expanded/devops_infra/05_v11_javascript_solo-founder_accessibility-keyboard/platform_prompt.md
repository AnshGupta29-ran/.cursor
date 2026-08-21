# VARIANT v11_javascript_solo-founder_accessibility-keyboard - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `javascript`
- **user_persona**: `solo_founder`
- **novelty_hook**: `accessibility_keyboard`
- **ui_surface**: `cli_tui`
- **persistence**: `sqlite`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `javascript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v11_javascript_solo-founder_accessibility-keyboard`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v11_javascript_solo-founder_accessibility-keyboard` when demoable.

---

## BASE PRD (honor unless mutated above)

# StrataLens — Terraform State Explorer & Diff Console

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `html_canvas`
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


## 1. Project Request / Product Identity

**StrataLens** is a local-first console for staff engineers who review Terraform changes *after* apply, not before. It ingests raw `.tfstate` JSON, indexes every resource instance into SQLite, renders the dependency graph on an HTML `<canvas>`, and produces an address-precise diff between any two loaded snapshots (e.g., pre-incident vs. post-incident state). Think "git diff for infrastructure reality," with a blast-radius highlighter. Actions never touch real infrastructure — this is an inspection and forensics tool, and the UI must say so.

## 2. Target Users & Primary Jobs-to-be-Done

- **Staff engineer reviewing a teammate's apply**: "What actually changed between Tuesday's state and today's, down to the attribute?"
- **On-call doing incident forensics**: "Which resources depend on the `aws_security_group.egress` that just got replaced — show me the blast radius."
- **Engineer annotating a migration**: pin a note to a resource address ("moved to module.dns in PR #412") that survives snapshot reloads.

## 3. Core Requirements / Entities

Python 3.10+, SQLite (stdlib `sqlite3` is fine), server-rendered HTML + vanilla JS with a `<canvas>` graph. Suggested: Flask or stdlib `http.server`; **no frontend build step, no heavy deps**.

- **Snapshot**: id, name, source filename, `terraform_version`, `serial`, `lineage`, resource count, created_at, raw JSON blob.
- **ResourceInstance** (derived at parse time, may be recomputed): snapshot_id, full address (`module.vpc.aws_subnet.web["a"]`), type, name, mode (`managed`/`data`), provider, tainted/deposed flags, attributes JSON, dependencies list.
- **ResourceNote**: address, body, created_at (keyed by address so notes persist across snapshots).
- **DiffRun**: base_snapshot_id, head_snapshot_id, counts (added/removed/changed/unchanged), created_at.
- **AuditEvent**: action (`snapshot.load`, `snapshot.delete`, `diff.run`, `note.add`), detail, created_at.

Parser targets **raw .tfstate format v4** (`resources[]` with `instances[]`, including `index_key`, `status: tainted`, `deposed`). Detect `terraform show -json` output and reject it with an explicit "format detected: show-json; unsupported" message.

## 4. Major Feature Areas

- **Snapshot ingest**: upload file or paste JSON; validate, parse, persist, audit. Reject >25 MB with a clear error.
- **Inventory view**: ops-dense table — address, type, provider, mode, tainted/deposed badge, note indicator; filter by substring, module path, type, status.
- **Attribute inspector**: click a row → drawer with a collapsible JSON tree of instance attributes; values marked `sensitive` in state are masked as `••••••` with a per-field reveal toggle.
- **State diff**: pick base + head snapshots → summary counts + per-resource table (added/removed/changed/unchanged) + recursive attribute-level old/new values (long values truncated at 200 chars with expand). Export diff as JSON and as Markdown.
- **Canvas dependency graph**: nodes = resource instances, edges from `dependencies` arrays, simple layered topological layout; color-coded by diff status (green added / red removed / amber changed / gray unchanged); click node → inspector; **Blast Radius** toggle highlights all transitive dependents of the selected node.
- **Notes**: add/list/delete notes per address; shown in inspector and as badges in inventory.
- **Live demo mode**: `STRATALENS_DEMO=1` seeds two fixture snapshots (`shopfront-v1`, `shopfront-v2`) with a module move, one tainted resource, an added autoscaling group, a changed instance type, and two pre-written notes — so inventory, diff, graph, and blast radius are all interesting within one click. A banner labels demo mode.

## 5. Domain-Specific Workflows

**Happy path**: start in demo mode → open Diff of v1→v2 → click changed `aws_instance.app` → inspector shows `instance_type: t3.micro → t3.large` → toggle Blast Radius on canvas → add note → export Markdown diff.

**Edge cases**: invalid JSON (HTTP 422 + parse position); show-json detected (explicit unsupported-format error); state with zero resources (empty state with hint to run `terraform state pull`); diffing a snapshot against itself ("states identical" view, no crash); missing `dependencies` (node renders orphan-styled); deleting a snapshot referenced by a DiffRun (confirm dialog; DiffRun kept with tombstoned reference).

## 6. Data & Persistence

SQLite file at `./stratalens.db` (path via env var). Raw state JSON stored once per snapshot; parsed instances recomputed on read or cached in a table — implementer's choice. Notes and AuditEvents must survive snapshot deletion. Trusted-local mode: bind `127.0.0.1` by default, no auth; README must state this explicitly and warn that state files contain secrets.

## 7. UX / API Surface

Single-page ops console: left = inventory/diff tables, right = inspector drawer, top = canvas graph panel. Color semantics documented in README. Endpoints (suggested): `POST /api/snapshots`, `GET /api/snapshots`, `DELETE /api/snapshots/{id}`, `GET /api/snapshots/{id}/resources`, `POST /api/diffs`, `GET /api/diffs/{id}?format=markdown|json`, `POST/DELETE /api/notes`. Errors return `{error, detail, detected_format?}`.

## 8. Quality, Security, Reliability

Pure-JSON parsing only — **never shell out to `terraform`**. Upload size cap, request timeouts, and a UI that keeps inventory usable if graph rendering throws (canvas failure must not blank the page). Sensitive-attribute masking is server-side for API responses unless `?reveal=1` is passed.

## 9. Documentation & Testing

README: quickstart, demo-mode instructions, `terraform state pull > state.json` primer, security notes, optional `docker-compose.yml` (app + volume for the DB — must remain optional; app runs with `python app.py`). Light unit tests (`pytest` or `unittest`): v4 parser flattens modules/index_keys correctly; diff engine classifies added/removed/changed with attribute-level deltas; sensitive masking; invalid-upload error path. `pytest -q` green in seconds.

## 10. Constraints & Non-Goals

No plan-file parsing, no `terraform` binary invocation, no remote-state backends (S3/Cloud), no multi-user auth, no editing/applying state. Not a Terraform Cloud replacement.

## 11. Acceptance Criteria

- [ ] Upload/paste of a v4 tfstate creates a snapshot and populates inventory
- [ ] Diff of two snapshots shows correct counts + attribute-level changes, exportable as JSON and Markdown
- [ ] Canvas graph renders dependencies; Blast Radius highlights transitive dependents
- [ ] Tainted/deposed resources are visually flagged; sensitive values masked by default
- [ ] Demo mode seeds two fixtures and is labeled; every feature demoable without user data
- [ ] show-json and malformed uploads fail with explicit, distinct errors
- [ ] Snapshot delete requires confirmation; notes and audit events persist
- [ ] Unit tests pass; README demo script succeeds

## 12. Uniqueness / Anti-Clone Constraints

This is **not** a generic JSON viewer or another Docker dashboard: Terraform vocabulary (`address`, `serial`, `lineage`, `tainted`, `deposed`, `module.` paths, `index_key`) must appear throughout the UI and code. The canvas dependency graph with diff-colored blast radius is mandatory, not optional. No placeholder lorem-ipsum panels; fixture data must be a coherent fictional shopfront infrastructure, not `foo`/`bar` resources.
