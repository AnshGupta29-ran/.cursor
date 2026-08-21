# VARIANT v44_cpp_security-auditor_idempotent-retries - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `cpp`
- **user_persona**: `security_auditor`
- **novelty_hook**: `idempotent_retries`
- **ui_surface**: `api_only`
- **persistence**: `localstorage`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `cpp`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v44_cpp_security-auditor_idempotent-retries`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v44_cpp_security-auditor_idempotent-retries` when demoable.

---

## BASE PRD (honor unless mutated above)

# DryDock — Local Container Registry Stub & Cleanup-Policy Playground

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `rust`
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
Build **DryDock**: an offline-first, memory-only practice copy of a container image registry — the service where build tools store versioned app artifacts ("images"). DryDock lets a developer or instructor safely explore tag deletion and garbage-collection (GC) cleanup rules and watch storage get reclaimed — **no cloud accounts, no Docker Hub, no risk to a real registry**.

Because real registries age over months, DryDock ships a **virtual clock**: a simulated "now" the operator advances by hours/days, so rules like "collect untagged items older than 14 days" are demonstrable in a 60-second demo.

**Locked stack** (do not change): Rust backend (axum or actix-web) exposing a JSON REST API and serving a React SPA (Vite + TypeScript). Persistence is in-memory only — no database, no runtime file writes. Delivery is exactly one documented command (e.g. `./dev.sh`) that builds the SPA if needed and starts the server on localhost. The app must boot and pass a live runtime smoke run.

## 2. Target users & jobs-to-be-done
- **Solo developer** evaluating cleanup rules before enabling them at work: "Show me exactly which tags, manifests, and bytes a keep-last-5 policy would delete."
- **Instructor / workshop lead**: demo the lifecycle push → delete tag → orphaned manifest → GC sweep live, advancing virtual time between steps.
- **Non-technical PM**: read the dashboard and audit log and understand, in plain words, what was reclaimed and why.

## 3. Core entities (domain-authentic names required)
- **Repository** — named image collection (e.g. `payments/api`).
- **Tag** — movable label (`v1.4.0`, `latest`) pointing at a manifest digest.
- **Manifest** — immutable image description addressed by digest (`sha256:…`); has virtual createdAt/lastPulledAt; becomes **untagged** when its last tag is deleted.
- **Blob** — stored layer chunk with size and reference count; zero referrers = reclaimable.
- **GCPolicy** — ordered rules: (a) keep the N most recent tags per repo, (b) protect tags matching patterns (`latest`, `*-release`), (c) collect untagged manifests older than X virtual days, (d) sweep unreferenced blobs.
- **AuditEvent** — actor, action, virtual timestamp, counts and bytes for every mutation.
- **VirtualClock** — single source of "now"; forward-only.

## 4. Major feature areas
- **Fixture seeder**: "Dock fixture fleet" loads ≥4 repos, ≥25 tags, several already-untagged manifests, several zero-ref blobs, ages spread across ~90 virtual days.
- **Inventory**: repo list (name, tag count, total bytes, untagged count, last activity) and repo detail (tag table: name, short digest, size, age, last pulled, protected?). Search/filter by name and status.
- **Tag delete** with typed confirmation; deleting the final tag flips the manifest to untagged, clearly announced in the UI.
- **GC policy editor**: form covering all four rule types; invalid rules rejected with plain-language messages.
- **Dry-run preview**: plan grouped by reason (age-expired, beyond-keep-N, unreferenced blob) with item and byte totals; deletes nothing.
- **Run GC**: confirmation → execute → reclaimed bytes/counts report → AuditEvent written.
- **Virtual clock banner**: always visible; +1 hour / +1 day / +7 days controls; all ages derive from it.
- **Audit trail panel** and **read-only mode toggle** disabling every mutating control (with tooltip).
- **Reset**: restore seeded state.

## 5. Domain workflows
**Happy path**: seed → open repo → delete an old tag (confirm) → advance clock 7 days → edit policy → dry-run → inspect grouped preview → run GC → see reclaimed bytes → audit shows the run.
**Edge cases**: deleting a manifest's last tag; `latest` protected even when old; keep-N applies per repository, not globally; GC with nothing to collect returns a friendly zero-result (not an error); deleting a nonexistent tag surfaces a 404 in the UI; clock cannot move backwards.

## 6. Data & persistence
In-memory store behind a trait; seeded at boot; `POST /api/reset` restores fixtures. Nothing survives restart — say so in the README and UI footer. No accounts or tokens: explicit **trusted-local mode** (localhost only).

## 7. UX / API surface
REST JSON under `/api`: `GET /health`, `GET /repositories`, `GET /repositories/{name}/tags`, `DELETE /repositories/{name}/tags/{tag}`, `GET|PUT /gc/policy`, `POST /gc/dry-run`, `POST /gc/run`, `GET /audit`, `GET|POST /clock`, `POST /seed`, `POST /reset`.
SPA screens: Repositories, Repository detail (tags + dry-run drawer), Policy, Audit. Documented status colors (protected=blue, expiring=amber, collectable=red, reclaimed=green). If the API is unreachable, show a clear error banner with retry — never a blank page.

## 8. Quality, security, reliability
GC planning is a pure function `(store snapshot, policy, now) → plan` — unit-test it heavily. Validate repo/tag/policy inputs; reject path-like or oversized strings. No shelling out, no network egress, no Docker socket. Destructive endpoints require explicit confirm flags. Errors return structured JSON the SPA renders verbatim; one failing panel must not freeze the rest of the UI.

## 9. Documentation & testing
README: prerequisites (Rust, Node), the single run command, a plain-language glossary (tag, manifest, blob, GC), the 60-second demo script, safety notes. Tests: `cargo test` covering GC rules, tag-delete semantics, blob refcounts, and API handlers against the in-memory store; SPA must build cleanly. `scripts/smoke.sh` boots the server, seeds, lists repos, dry-runs, runs GC, and asserts reclaimed bytes > 0 plus a matching audit entry.

## 10. Constraints & non-goals
Not a real OCI registry: no `docker push/pull` wire protocol, no authNZ, no multi-node, no disk storage, no cloud integrations. Build nothing beyond section 4.

## 11. Acceptance criteria
- [ ] One command starts backend + SPA on localhost; works fully offline after dependency install
- [ ] Seeder produces the fixture fleet described above
- [ ] Tag list shows digest/size/age/last-pulled; search + status filter work
- [ ] Tag delete requires confirmation; last-tag deletion marks manifest untagged
- [ ] All four GC rule types configurable; invalid rules rejected with messages
- [ ] Dry-run shows grouped plan with totals and mutates nothing
- [ ] GC run reclaims bytes, updates inventory, appends an AuditEvent
- [ ] Clock advances; ages and GC outcomes change; backwards rejected
- [ ] Read-only toggle disables every mutating control
- [ ] Reset restores seeded state
- [ ] `cargo test`, SPA build, and `scripts/smoke.sh` all pass against the running server

## 12. Uniqueness / anti-clone constraints
Keep the DryDock nautical identity (or invent an equally specific one — not "registry-app" or "image-manager"). UI copy must use registry vocabulary (digest, manifest, blob, untagged, reclaim) and include the virtual-clock concept; a generic CRUD table with renamed columns fails review. No placeholder pages, no lorem ipsum, no "Todo" patterns, no signup/login screens.
