# Category batch FORGED: devops_infra (10/10) — paste into Chakra

Each task is a forged PRD with a **locked dimension mix**. Implementing these under
`harness/chakra/task_devops_infra_NN/` produces synthetic agent trajectories for stats.

**Playing/demoing alone is NOT datagen** — datagen is the implement session.

## Dimension coverage

| # | complexity | value | language | UI | persistence | verification |
|---|------------|-------|----------|----|-------------|--------------|
| 01 | medium | medium | python | mobile_web | postgres_optional | browser_smoke |
| 02 | low | medium | go | static_html | memory_only | static_pass |
| 03 | hard | hard | typescript | game_loop_window | sqlite | runtime_pass |
| 04 | low | low | python | cli_tui | json_file | static_pass |
| 05 | medium | medium | python | html_canvas | sqlite | unit_tests |
| 06 | hard | hard | rust | react_spa | memory_only | runtime_pass |
| 07 | low | medium | javascript | desktop_window | localstorage | browser_smoke |
| 08 | hard | hard | java | static_html | csv_files | visual_diff |
| 09 | medium | low | go | api_only | sqlite | unit_tests |
| 10 | hard | hard | typescript | excel_workbook | json_file | runtime_pass |

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

## Task 01 — Docker container management dashboard
**workdir:** `task_devops_infra_01`
**id:** `devops_infra_01_docker-container-management-dashboard`
**seed (original):** Build a Docker container management dashboard that interacts with the Docker Engine API to start, stop, inspect, and monitor containers.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "resume_mid_task", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "devops_ops", "business_domain": "devops_platform", "ui_surface": "mobile_web", "persistence": "postgres_optional", "testing_depth": "browser_smoke", "novelty_hook": "plugin/extension hook (one stub plugin)", "delivery": "monorepo_client_server", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# QuayWatch — Mobile-First Docker Triage Console with Audit & Plugin Findings

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

**QuayWatch** is a mobile-web console for on-call operators who must triage a Docker host from a phone: glance at fleet health, spot restart storms, read a log tail, and take one safe action — with every mutation written to an audit trail. It speaks to the Docker Engine API when available and ships a rich **simulator mode** so the product is fully demonstrable without a Docker daemon.

Differentiator (not another Docker dashboard): QuayWatch is **audit-first and governance-flavored** — destructive actions require typed confirmation, every mutation is persisted, and a **plugin hook** lets teams attach compliance "findings" to containers. One stub plugin (`privilege_lint`) ships in-repo.

**Stack (locked):** Python 3.10+ (FastAPI suggested), server-rendered mobile-web UI (Jinja2 templates + vanilla JS or htmx; no SPA build step). Monorepo: `server/` (API + UI serving) and `web/` (templates/static), plus `plugins/` and `tests/`. Persistence: SQLite by default, Postgres via `DATABASE_URL` (SQLAlchemy/ORM — switch must be config-only).

## 2. Target Users & Jobs-to-be-Done

- **On-call operator (primary):** "Something is down — show me unhealthy containers, let me read logs, restart one, and prove I did it." Mobile viewport is the design target (360px wide).
- **Platform lead / enterprise buyer (voice for tone):** wants a defensible audit trail, a read-only enforcement mode, and an extension point for internal policy checks.

## 3. Core Requirements / Entities

- **ContainerView** (live from Engine/simulator, not persisted): id, name, image, status/state, restart count, created age, ports, health.
- **AuditAction** (persisted): timestamp, actor, action (`start|stop|restart|remove`), target container name/id, outcome (`success|rejected|error`), detail message, mode (`live|simulator`).
- **Finding** (persisted per scan or computed at request time): container ref, plugin name, severity (`info|warn|critical`), message (e.g., "runs privileged").
- **Plugin contract:** a plugin is a Python module in `plugins/` exposing `on_container(container_dict) -> list[Finding]` and optional `actions() -> list[dict]`. Loaded via a small registry at startup; failures in one plugin must not break the app (log + skip).

## 4. Major Feature Areas

- **Fleet inventory:** card/list layout of containers with status color semantics (green=running, amber=restarting/unhealthy, red=exited, gray=paused), search/filter by name, image, and state; sort by restarts or age.
- **Restart-storm detector:** banner/badge on any container with ≥3 restarts within a 10-minute window (computed from Engine state or simulator fixtures).
- **Detail drawer:** metadata (image, env count, mounts, networks), recent state, and a **log tail** (last ~100 lines) fetched on demand with refresh; failing log fetch degrades that panel only, never the page.
- **Actions:** start, stop, restart, remove — each with confirmation; remove and stop require the operator to **type the container name** into the confirm dialog. Engine rejections surface as inline error toasts with the API message.
- **Findings panel:** per-container findings from loaded plugins; stub plugin `privilege_lint` flags privileged mode, root user, and `:latest` tags.
- **Audit log view:** reverse-chronological table of mutations with mode and outcome.

## 5. Domain Workflows

**Happy path:** open on phone → fleet list loads → filter to `exited` → open detail → read log tail → type-name confirm **restart** → success toast → entry appears in Audit Log labeled `simulator` or `live`.

**Edge cases:** (a) Engine unreachable → persistent banner "Docker unavailable — showing simulator fixtures" with fix hint (`DOCKER_HOST` note); all mutations still work against simulator and are audited as `simulator`. (b) Action rejected (e.g., remove running container) → error toast, audit row with outcome `rejected`. (c) Read-only mode on → all mutating controls disabled with an explainer tooltip. (d) Plugin raises → finding badge shows "plugin error", app unaffected.

## 6. Data & Persistence

SQLAlchemy models for `AuditAction` (and `Finding` if persisted); SQLite file by default; setting `DATABASE_URL=postgresql://...` must work with zero code changes. Live container state is **never** persisted as source of truth — the Engine (or simulator) is. Simulator fixtures live in `server/simulator/fixtures.json` (≥8 containers covering running/exited/restart-storm/unhealthy states).

## 7. UX / API Surface

Mobile-web first: single-column layout, large tap targets, sticky filter bar, dark ops theme. JSON API under `/api/`: `GET /api/containers`, `GET /api/containers/{id}`, `GET /api/containers/{id}/logs?tail=100`, `POST /api/containers/{id}/{start|stop|restart|remove}`, `GET /api/audit`, `GET /api/findings`, `GET /api/health`. Status colors and mode badge (`LIVE`/`SIM`) visible on every screen.

## 8. Quality, Security & Reliability

Trusted-local mode by default (stated in README); optional `QUAYWATCH_ADMIN_TOKEN` bearer check on mutating routes. `QUAYWATCH_READONLY=1` hard-disables mutations server-side. Never shell out — Docker SDK/HTTP client only, with short timeouts (≤5s) and mapped error responses. One failing log stream or plugin must not freeze the UI.

## 9. Documentation & Testing

README: prerequisites, simulator vs live setup, env vars, plugin authoring example, and a 60-second demo script (inspect → restart → verify in audit). Tests: `pytest` suite with a **mocked Docker client** covering action authorization, read-only rejection, engine-error mapping, and the plugin registry; plus `scripts/smoke.py` — a browser-smoke style check that boots the server in simulator mode and asserts the fleet page, one detail/logs call, one audited restart, and the audit endpoint all return 200 with expected content.

## 10. Constraints & Non-Goals

Not a Kubernetes console, not multi-host, not cluster provisioning, not a metrics/graphing platform. No SPA framework, no Node build, no heavy dependencies. Auth beyond the optional token is out of scope.

## 11. Acceptance Criteria

- [ ] Fleet list, filters, and status colors render on a 360px viewport in simulator mode.
- [ ] Restart-storm badge appears on fixture data.
- [ ] Start/stop/restart/remove work; remove/stop require typed-name confirmation.
- [ ] Log tail loads for one container; a failing log call degrades gracefully.
- [ ] Every mutation writes an `AuditAction` row visible in the audit view with mode label.
- [ ] `privilege_lint` stub plugin produces ≥1 finding on fixtures; a broken plugin does not crash the app.
- [ ] Read-only env flag blocks mutations server-side; optional token auth works.
- [ ] Engine-down banner with fix hint appears when Docker is absent.
- [ ] `pytest` passes with mocked Docker client; `scripts/smoke.py` exits 0.
- [ ] README demo script succeeds in simulator mode; `DATABASE_URL` Postgres switch documented.

## 12. Uniqueness / Anti-Clone Constraints

This is **not** a generic CRUD board or "Todo with containers." Required distinctive elements: typed-name destructive confirmation, restart-storm detection, audit-first mutation log with live/sim labeling, read-only governance mode, and the plugin findings hook with the `privilege_lint` stub. Use ops-authentic terminology (fleet, finding, audit trail, restart storm) throughout the UI; no lorem ipsum, no placeholder cards — all fixture data must look like a plausible production host.

When done, print `DONE task_1: Docker container management dashboard` and start the next task immediately.

---

## Task 02 — Kubernetes cluster visualization
**workdir:** `task_devops_infra_02`
**id:** `devops_infra_02_kubernetes-cluster-visualization`
**seed (original):** Build a Kubernetes cluster visualization dashboard that displays nodes, pods, deployments, services, logs, and resource utilization using the Kubernetes API.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "go", "artifact_type": "web_fullstack", "task_family": "devops_ops", "business_domain": "devops_platform", "ui_surface": "static_html", "persistence": "memory_only", "testing_depth": "smoke_only", "novelty_hook": "multi-theme or multi-difficulty presets", "delivery": "library_plus_demo_app", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# Project Request / Product Identity

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## Target Users & Jobs-to-be-Done

A solo dev practicing cluster triage or demoing K8s concepts without a real kubeconfig. Primary jobs: (1) glance at node/pod/deployment/service health in one dense page, (2) spot which workload is misbehaving via utilization sparklines, (3) perform a safe mutating action (restart/scale/delete pod) and watch state change, (4) read a pod's recent log tail.

## Core Requirements / Entities

In-memory structs (no DB, no files): `Node` (name, capacity, conditions), `Pod` (name, namespace, node, phase, container statuses, restartCount, labels, owner deployment), `Deployment` (replicas desired/ready), `Service` (type, clusterIP, selector, ports), `Event` (timestamp, object ref, reason, message), `MetricSample` (per-node and per-pod CPU%/mem% time series, fixed-size ring buffer), and `AuditAction` (timestamp, action, target, result) logged for every mutation.

## Major Feature Areas

- **Simulator engine (`pkg/pulse`)**: seeds a realistic fixture cluster (3 nodes, ~12 pods, 4 deployments, 3 services) and ticks every ~2s, advancing metrics and pod phases. Scenario presets: `calm` (stable), `degrading` (one deployment's pods flap, memory creeps), `incident` (node NotReady + CrashLoopBackOff storm). Preset switchable via UI and env var.
- **Inventory dashboard**: server-rendered tables for nodes, pods, deployments, services with status, age, restarts; filter pods by namespace/status via query param; color semantics (green=Ready/Running, amber=Pending/Degraded, red=Failed/NotReady/CrashLoopBackOff) documented in README.
- **Charts**: inline SVG sparklines (no external JS/CDN) for cluster CPU% and memory% over the last 60 ticks, plus per-node utilization bars.
- **Detail view**: per-pod page with metadata, owner, recent events, and last ~40 log lines (simulated logs generated by the engine, refresh on load).
- **Actions**: restart pod, scale deployment (±1), delete pod. Delete requires a confirm form step. Every action writes an `AuditAction`, surfaced in an "Operator actions" panel.
- **Themes**: three CSS themes toggled via query param/cookie-free header link; default midnight.

## Domain Workflows

Happy path: open dashboard → see incident preset's red pods → open pod detail → read logs → restart pod → audit panel records it → pod cycles Pending→Running on next ticks → sparkline recovers. Edge cases: acting on a just-deleted pod returns a clean 404-style error banner; scaling below 0 or above 10 is rejected with a message; unknown pod name in detail/logs returns friendly "object not found" page; simulator tick failure must not hang page render.

## Data & Persistence

Memory only — all state lives in process; restart resets to seeded fixture. No disk writes, no sessions, no auth (explicit **trusted-local mode**: binds to 127.0.0.1 by default; README states this posture).

## UX / API Surface

Routes (stdlib `net/http` only; no frameworks, no external deps beyond the Go toolchain): `GET /` dashboard, `GET /pods/{name}` detail+logs, `POST /pods/{name}/restart`, `POST /pods/{name}/delete` (with `GET /pods/{name}/delete` confirm page), `POST /deployments/{name}/scale?delta=`, `GET /healthz`. JSON is not required; HTML is the product. One smoke test spins the server via `httptest` and asserts dashboard renders seeded pods and a restart action mutates state.

## Quality, Security & Reliability

No shelling out. No client-go dependency in the MVP (simulator stands behind a `ClusterSource` interface so a real adapter could be added later). Handlers must not panic on missing objects; mutations are mutex-guarded. `go vet` clean and `gofmt` clean (static verification mode).

## Documentation & Testing

README: prerequisites (Go 1.22+), run instructions, scenario preset descriptions, theme list, safety posture (trusted-local, simulated data), and a 5-step demo script (inspect → filter → logs → restart → verify in audit panel). One smoke test file; `go test ./...` must pass.

## Constraints & Non-Goals

Not a real cluster controller; no live kubeconfig support, no YAML apply, no multi-cluster, no websockets/SSE (plain page refresh is fine). Keep total footprint ~6–9 Go files. No placeholder-only pages; every table must render simulator-authentic K8s terminology (CrashLoopBackOff, clusterIP, nodeAffinity, etc.).

## Acceptance Criteria

- [ ] `go run ./cmd/kubepulse` serves a dashboard listing seeded nodes, pods, deployments, services
- [ ] Three scenario presets selectable and visibly change cluster behavior within ~10s
- [ ] Three UI themes selectable
- [ ] CPU/mem sparklines + per-node bars render as inline SVG
- [ ] Pod detail shows events and log tail
- [ ] Restart, scale, and delete work; delete requires confirmation; all appear in audit panel
- [ ] "SIMULATED CLUSTER" banner visible; missing-object and bad-scale errors shown cleanly
- [ ] `go vet ./...`, `gofmt -l .` clean; `go test ./...` smoke test passes
- [ ] README demo script succeeds as written

## Uniqueness / Anti-Clone Constraints

Must not be a generic "Docker dashboard" or tutorial CRUD clone. The KubePulse identity, scenario-preset simulator (calm/degrading/incident), theme presets, audit panel, and server-rendered SVG sparklines are required distinguishing features. No Todo-style scaffolding, no lorem ipsum, no unused stub routes.

When done, print `DONE task_2: Kubernetes cluster visualization` and start the next task immediately.

---

## Task 03 — GitHub-like code repository platform
**workdir:** `task_devops_infra_03`
**id:** `devops_infra_03_github-like-code-repository-platform`
**seed (original):** Build a GitHub-like code repository platform with repository browsing, issues, pull requests, authentication, and Markdown rendering.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "approval_gated", "repo_state": "partial_scaffold", "tool_profile": "mixed", "user_persona": "staff_eng", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "game_loop_window", "persistence": "sqlite", "testing_depth": "unit_plus_smoke", "novelty_hook": "chaos toggle: inject one recoverable failure path", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# Trainyard — Merge-Train Code Review Console

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
Build **Trainyard**, a TypeScript web platform where a small platform team reviews code and dispatches merges through a **merge train**. It combines repository browsing, issues, pull requests, approvals, and Markdown rendering with a live **ops deck**: a continuously re-rendering "rail yard" window (game-loop style render tick + polled state) showing train slots, signal states, and an audit event ticker. Persistence is **SQLite**. A first-class **chaos toggle** injects one recoverable failure (signal fault) into the train so operators can drill recovery. Audience is staff engineers: be terse, explicit about invariants, no toy UI.

## 2. Target users & primary jobs-to-be-done
- **Maintainer**: triage issues/PRs, approve reviews, board the train, recover blocked slots.
- **Viewer** (read-only): browse repos, watch the deck.
Jobs: "see everything about to land at a glance", "gate merges on approval", "recover from a flaky check with zero data loss".

## 3. Core entities (SQLite)
- `Operator(id, handle, password_hash /* scrypt */, role: maintainer|viewer)`
- `Repository(id, slug, name, description, default_branch)`
- `RepoFile(repo_id, branch, path, content, updated_at)` — virtual tree, seeded fixtures; **no git shelling**
- `Issue(id, repo_id, number, title, body_md, status: open|closed, author_id, created_at)`
- `PullRequest(id, repo_id, number, title, body_md, source_branch, target_branch, status: OPEN|MERGED|CLOSED, author_id)`
- `Review(pr_id, operator_id, state: APPROVED|CHANGES_REQUESTED, UNIQUE(pr_id, operator_id))`
- `MergeSlot(id, pr_id, position, state: QUEUED|CHECKING|DISPATCHED|BLOCKED_RECOVERABLE, attempts, last_error)`
- `Comment(id, target_type: issue|pr, target_id, author_id, body_md, created_at)`
- `AuditEvent(id, actor, action, target, payload_json, created_at)` — append-only
- `ChaosFlag(id=1, enabled, updated_by)`

## 4. Major feature areas
- **Auth**: register/login/logout/me; scrypt+salt hashing; HttpOnly `SameSite=Lax` session cookie; viewers get 403 on any mutation. First registered operator becomes maintainer.
- **Repo browsing**: repo list; per-repo file tree (flat path list acceptable) and file content view; default branch only.
- **Issues**: list (filter open/closed, search title), create, close/reopen, comment; Markdown bodies.
- **Pull requests**: list/create/close; detail shows body, reviews, train state. Reviews: approve / request-changes (upsert per operator).
- **Merge train**: enqueue PR (approval-gated); a server tick (~2s) advances slots FIFO: `QUEUED→CHECKING→DISPATCHED`, then marks the PR `MERGED`. Retry endpoint for blocked slots.
- **Chaos toggle**: maintainer-only `POST /api/chaos {enabled}`. While enabled, each `CHECKING` transition has probability `p` (env `CHAOS_P`, default 0.5, injectable in tests) to land in `BLOCKED_RECOVERABLE` with `SIGNAL_FAULT`. Retry re-enters `CHECKING`. Failure is recoverable: no partial merges, transitions transactional.
- **Markdown**: render issue/PR/comment bodies server-side with a small MD library; sanitize output (strip scripts/`on*` attrs); store raw MD.
- **Audit**: every mutation writes an `AuditEvent`; deck ticker streams the tail.

## 5. Domain workflows
**Happy path**: register → seeded repos present → open PR → a second maintainer approves → enqueue → deck animates slot through signals → `DISPATCHED` → PR `MERGED`; audit events stream.
**Edge cases**: author self-approval → 409; enqueue without ≥1 non-author `APPROVED` → 409; open `CHANGES_REQUESTED` blocks enqueue until superseded; chaos fault → amber signal + retry succeeds; DB write failure → 500 surfaced, slot state unchanged; ≥3 consecutive poll failures → `STALE` banner while UI keeps rendering last snapshot.

## 6. Data & persistence
SQLite file (`data/trainyard.db`) via `better-sqlite3` or equivalent; WAL mode; schema + seed auto-applied on boot when empty (2 repos, ~12 files, 3 issues, 2 PRs, one maintainer + one viewer demo account documented in README). Indexes on `(repo_id, number)` for issues/PRs and `MergeSlot(position)`. Audit reads capped (`LIMIT 200`).

## 7. UX / API surface expectations
Single-page deck (Vite + TypeScript; React optional). **Game loop**: poll `GET /api/deck` (aggregate snapshot: train slots, signal states, counts, audit tail) every 2s; `requestAnimationFrame` render tick animates slot movement and signal blink; interaction via clickable panels and a PR detail drawer — functional console, not a fake game. Panels: **Yard** (train), **Repos**, **Issues**, **PR detail**, **Event ticker**. Rail-yard terminology in labels ("Dispatch", "Signal", "Blocked — Retry"). Destructive actions (close PR, dequeue slot) require a confirm dialog. REST JSON under `/api/*`; consistent error shape `{error, code}`; correct 401/403/409/422 semantics.

## 8. Quality, security, reliability
All train state changes in transactions. **Invariant: a PR is `MERGED` iff its slot reached `DISPATCHED`.** Sanitized Markdown (XSS test mandatory). No shelling to git or arbitrary system commands. Deck snapshot must avoid N+1 queries. In-memory throttle on login. Chaos RNG injectable for deterministic tests.

## 9. Documentation & testing
README: one-command quickstart (`npm install && npm run dev` → single port, schema+seed automatic), demo script (inspect → approve → board → chaos on → recover → merged), roles/accounts, chaos design note, API summary. Tests (Vitest): **unit** — scrypt verify, approval gate, chaos injector with forced RNG, Markdown sanitizer, FIFO ordering; **smoke** — boot server on ephemeral port, drive the full happy path including chaos recovery over HTTP, assert final `MERGED` (`npm run smoke`, <30s).

## 10. Constraints & non-goals
No real git, no diffs/patches, no webhooks, no multi-branch browsing, no orgs, no external CI ("checks" are simulated by the train tick). Not a GitHub-clone checklist exercise.

## 11. Acceptance criteria
- [ ] `npm run dev` boots API+UI on one port with schema+seed, zero manual steps
- [ ] Register/login/logout work; viewers cannot mutate (403)
- [ ] Seeded repo tree + file contents browsable
- [ ] Issues create/close/comment with sanitized Markdown
- [ ] PR create/close/review; self-approval and approval-less enqueue rejected (409)
- [ ] Train processes FIFO; PR reaches `MERGED` only via `DISPATCHED`; mutations audited
- [ ] Chaos toggle yields recoverable `BLOCKED_RECOVERABLE`; retry completes the merge with no partial state
- [ ] Deck polls and re-renders live; stale banner on poll failure
- [ ] Unit + smoke suites pass; smoke covers chaos recovery
- [ ] README demo script reproducible as written

## 12. Uniqueness / anti-clone constraints
Merge-train / rail-yard framing and terminology must pervade UI and API — a generic "GitHub clone with extra steps" fails review. The game-loop ops deck is the primary surface; a plain CRUD table UI fails. Chaos toggle is tested, not a stub. No placeholder pages, no `localStorage` persistence, no lorem-ipsum fixtures (seed plausible platform/infra repos). Repo may contain a partial scaffold — reconcile with it, don't blindly overwrite; plan module layout (`server / db / train / ui`) before writing code.

When done, print `DONE task_3: GitHub-like code repository platform` and start the next task immediately.

---

## Task 04 — CI pipeline status board
**workdir:** `task_devops_infra_04`
**id:** `devops_infra_04_ci-pipeline-status-board`
**seed (original):** Create a CI pipeline status board that ingests fake job events, shows stages, flaky detection, and retry buttons.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "single_shot", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "low", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "devops_ops", "business_domain": "devops_platform", "ui_surface": "cli_tui", "persistence": "json_file", "testing_depth": "smoke_only", "novelty_hook": "domain twist: niche audience + unusual constraint", "delivery": "single_readme_run", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# RigWatch — Bench CI Status Board for Solo Hardware Hackers

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

**RigWatch** is a terminal-only CI status board for a **solo firmware/hardware tinkerer** who runs self-hosted "bench rigs" (a Raspberry Pi flashing station, an FPGA build box, a thermal-loop tester) instead of cloud CI. There is **no server, no daemon, no network**: rigs append job events to an append-only `events.jsonl` drop file, and RigWatch renders a live board from it. Retrying a job means writing a **retry-request record to an outbox JSON file** that rigs poll on their own schedule — the unusual constraint is that the board *can never execute anything itself*, it can only file intent.

Stack lock: **Python 3.10+ stdlib only** (`curses`, `json`, `argparse`, `datetime`). Persistence: **JSON files**. Ship as a tiny package runnable via `python -m rigwatch`.

## 2. Target users & primary jobs-to-be-done

- Solo dev SSH'd into a headless lab box who wants "which rig failed and is it the flaky one again?" in one glance.
- Jobs: watch runs land live → drill into a failed stage → confirm whether a job is flaky vs. genuinely broken → file a retry → verify the retry landed in the outbox.

## 3. Core requirements / entities

- `JobEvent` (JSONL line): `ts, run_id, pipeline, stage, job, rig, event (queued|running|passed|failed|log), commit, message?`
- `Run` (derived): pipeline, commit, stages → jobs, overall status, duration.
- `FlakeRecord` (derived): per `(pipeline, job)` — outcomes of last 10 runs at the same commit-independent level; flake score.
- `RetryRequest`: `{ts, run_id, job, reason}` appended to `outbox.json`.
- `BoardState` (`state.json`): materialized runs + flake table, rebuilt from events on load.

## 4. Major feature areas

- **Ingest**: tail/load `events.jsonl`; tolerate malformed lines (count + show them, never crash).
- **Board view**: table of runs (pipeline, commit, rig, stage progress like `build✓ flash✓ bench✗`, age, status color).
- **Drill-down**: select run → stages → jobs; failed job shows last `message` log snippet.
- **Flaky detection**: a job is `FLAKY` if within its last 10 outcomes there are ≥2 failures *and* a pass–fail alternation (or fail-then-pass on same commit); score shown as e.g. `flaky 4/10`.
- **Retry**: key `r` on a failed/flaky job → confirm prompt → append `RetryRequest` to `outbox.json`; show "retry queued" marker until a newer event for that job arrives.
- **Demo mode**: `python -m rigwatch demo` generates a rich fixture event history (3 pipelines, incl. one genuinely broken job and one classic flaky `thermal-soak` job) then opens the board.
- **Snapshot mode**: `--once` renders the board as plain text and exits (non-interactive; used by smoke tests and CI-of-the-CI).

## 5. Domain-specific workflows

**Happy path**: `demo` → board shows runs → user selects failed `bench-test` run → sees `flash-verify` failed with log tail → flagged `FLAKY 3/10` → presses `r`, confirms → outbox gains a request → when a fake `passed` event lands (re-run `demo --append`), marker clears.

**Edge cases**: empty/missing events file → empty-state screen with fix hint ("no events.jsonl — run `python -m rigwatch demo`"); corrupt JSONL lines skipped with counter; outbox write failure surfaced as a status-bar error; retry on a passing job refused.

## 6. Data & persistence

All state lives in one directory (default `./rigwatch-data/`): `events.jsonl` (source of truth, append-only), `state.json` (materialized cache, safe to delete and rebuild), `outbox.json` (retry intents). Human-readable JSON; no DB, no binary formats. Rebuild-from-events must be idempotent.

## 7. UX surface

`curses` TUI with ops-dense tables; status semantics documented: green=passed, red=failed, yellow=running/queued, magenta=FLAKY badge, cyan=retry-queued. Keys: `↑/↓` select, `enter` drill, `r` retry, `R` reload events, `q` quit. Must degrade cleanly to `--once` text mode when `$TERM` is dumb or stdout is not a TTY.

## 8. Quality, security, reliability

- Never `shell out`; the board cannot execute anything — retries are file writes only.
- Board stays responsive if events file is truncated/rotated mid-read.
- Malformed events never lose good data.

## 9. Documentation & testing

`README.md`: one-command demo (`python -m rigwatch demo`), snapshot mode, file formats with example JSONL, key map, safety note ("RigWatch only writes retry intents; rigs decide"). Smoke test (`tests/smoke_test.py`): generate demo events → build state → assert flaky job is flagged and broken job is not → append retry → assert outbox record exists → run `--once` and assert exit 0. Plus `python -m compileall` static pass.

## 10. Constraints & non-goals

- Stdlib only; no pip installs, no real CI integrations (GitHub/GitLab), no auth (trusted-local, stated in README), no multi-user, no rig provisioning, no live process control.

## 11. Acceptance criteria

- [ ] `python -m rigwatch demo` produces fixture events and opens the board (or text fallback).
- [ ] Runs/stages/jobs render from `events.jsonl` with colors per semantics.
- [ ] Flaky detector flags the planted flaky job and not the consistently-failing one.
- [ ] Retry requires confirmation and appends to `outbox.json`; marker clears on new event.
- [ ] Empty and corrupt-events states handled with hints, no traceback.
- [ ] `python -m rigwatch --once` exits 0; smoke test passes; `compileall` clean.
- [ ] README run-through works exactly as written.

## 12. Uniqueness / anti-clone constraints

This is **not** a generic "CI dashboard tutorial": no web UI, no polling of real APIs, no todo-list mechanics. Must use bench-CI vocabulary (`rig`, `flash`, `bench-test`, `thermal-soak`) and honor the write-only-intent constraint — any feature that would require the board to execute or connect to something is out of scope. Placeholder UIs or lorem-ipsum events are forbidden; demo fixtures must tell a believable firmware-bench story.

When done, print `DONE task_4: CI pipeline status board` and start the next task immediately.

---

## Task 05 — Terraform state explorer
**workdir:** `task_devops_infra_05`
**id:** `devops_infra_05_terraform-state-explorer`
**seed (original):** Build a Terraform state explorer: load state JSON, list resources, show attributes, and diff two state files.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "devops_ops", "business_domain": "devops_platform", "ui_surface": "html_canvas", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "must include a live demo mode with sample data", "delivery": "docker_compose_optional", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# StrataLens — Terraform State Explorer & Diff Console

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

When done, print `DONE task_5: Terraform state explorer` and start the next task immediately.

---

## Task 06 — Local registry + image GC
**workdir:** `task_devops_infra_06`
**id:** `devops_infra_06_local-registry-image-gc`
**seed (original):** Create a local container image registry stub with tag list, delete, and garbage-collection policy demo.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "resume_mid_task", "repo_state": "partial_scaffold", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "rust", "artifact_type": "backend_api", "task_family": "devops_ops", "business_domain": "devops_platform", "ui_surface": "react_spa", "persistence": "memory_only", "testing_depth": "unit_plus_smoke", "novelty_hook": "offline-first; no cloud accounts", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# DryDock — Local Container Registry Stub & Cleanup-Policy Playground

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

When done, print `DONE task_6: Local registry + image GC` and start the next task immediately.

---

## Task 07 — Env var & secrets sync tool
**workdir:** `task_devops_infra_07`
**id:** `devops_infra_07_env-var-secrets-sync-tool`
**seed (original):** Build an env sync tool: compare .env across environments, redact secrets in diffs, and apply patches.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "multi_turn_repair", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "low", "value": "medium", "language_runtime": "javascript", "artifact_type": "cli_tool", "task_family": "devops_ops", "business_domain": "security_privacy", "ui_surface": "desktop_window", "persistence": "localstorage", "testing_depth": "integration_light", "novelty_hook": "accessibility-first keyboard UX", "delivery": "cli_entry_plus_ui", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# ParityPane — keyboard-first `.env` drift console

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project request / product identity
Build **ParityPane**: a local, fully offline console for release engineers at security-conscious enterprises who must prove environment variables match across `dev` / `staging` / `prod` before a deploy — without pasting secrets into a hosted diff SaaS. It ingests `.env` snapshots, renders a **redacted drift report**, and composes minimal **patches** to bring a target environment to parity.

- **Stack (locked):** vanilla JavaScript, Node ≥ 18, ES modules, **zero required npm dependencies**, no build step. Low complexity: ≤ 10 source files.
- **Delivery (locked):** CLI entry + UI. `bin/paritypane.mjs` serves the console over localhost and opens it in a dedicated desktop app window (Chrome/Edge `--app=` mode; Electron only if already installed — never a required install). The same static files must run standalone in any browser tab for smoke verification.
- **Persistence (locked):** browser `localStorage` (namespaced `paritypane:*`) is the system of record. No server-side DB. No telemetry, no network egress beyond localhost — this is the enterprise buying argument; state it in the README.

## 2. Target users & jobs-to-be-done
- **Release engineer:** "Show me which keys drifted between staging and prod — masked — and let me promote only the safe ones."
- **Security reviewer:** "Prove secrets never render in plaintext by default and that every reveal/apply is audit-logged."
- **Keyboard-driven operator:** complete the entire inspect → patch flow without touching a mouse.

## 3. Core entities
- `EnvironmentSnapshot { id, name, importedAt, sourceLabel, entries[] }`
- `EnvEntry { key, value, isSecret, fingerprint, line, warnings[] }`
- `DiffRow { key, status: same|changed|added|removed|empty, baseFp?, targetFp? }`
- `PatchOp { op: set|delete, key, value? }`
- `AuditEvent { ts, action, detail }` — import, reveal, diff, patch-apply, wipe
- `Settings { redactionMode: mask|last4|fingerprint, extraSecretPatterns[] }`

## 4. Major feature areas
- **Ingest:** paste box, multi-file picker, or CLI preload (`--env prod=.env.prod`, injected via a localhost seed endpoint and merged into localStorage on load). Parser handles comments, `export ` prefix, single/double quotes, blank lines, CRLF; duplicate keys → last wins + warning; malformed lines are listed, never fatal.
- **Secret detection & redaction:** key-name heuristics (`KEY|TOKEN|SECRET|PASS|PWD|CRED`) plus high-entropy value check; three redaction modes; SHA-256 fingerprint (first 10 hex via SubtleCrypto) so reviewers confirm equality without seeing values. Reveal is per-session, keyboard-gated (`R` on focused row), auto re-masks on window blur, and writes an AuditEvent.
- **Drift report:** pick base + target snapshots; grid of DiffRows with status chips; filter by status and substring; summary widgets (counts per status, missing-secret count, duplicate-key warnings).
- **Patch composer:** select rows with `Space` → masked unified-style preview → explicit confirmation → apply mutates the target snapshot in localStorage; dry-run summary line ("3 keys set, 1 removed on prod"); export patch as `.env` snippet or JSON ops.
- **Audit log:** reverse-chronological view (cap 200 events), export as JSON, and a **Lock & wipe** control that clears all `paritypane:*` keys.

## 5. Domain workflows
**Happy path:** `node bin/paritypane.mjs --env staging=fixtures/staging.env --env prod=fixtures/prod.env` → app window opens with both snapshots preloaded → operator tabs to env pickers → drift grid populates with an `aria-live` announcement → arrows navigate rows, `Space` selects changed keys → `P` opens patch preview → `Enter` confirms → success announced → audit log records the apply.

**Edge cases:** empty file → empty state with import hints; identical envs → "at parity" state; key present with empty value flagged `empty`; duplicate keys and malformed lines surface as warnings; localStorage quota failure → non-blocking toast; unknown CLI flags → non-zero exit with usage.

## 6. Data & persistence
Snapshots, settings, and audit log live only in localStorage. The CLI is stateless. README must document the threat model (plaintext secrets persist in localStorage until wipe) and the wipe control.

## 7. UX surface expectations
Accessibility-first keyboard UX is the product's signature and is non-negotiable: every feature operable by keyboard; `?` opens a shortcut cheatsheet dialog; `Cmd/Ctrl+K` command palette; drift grid uses roving tabindex with `role="grid"`; dialogs trap and restore focus; visible focus rings; `aria-live="polite"` for async results; `prefers-reduced-motion` respected; masked values carry screen-reader labels ("redacted, 18 chars, fp 9f2…"). Status color semantics documented in README (never color-only — pair with chips/text).

## 8. Quality, security, reliability
No external requests (CSP meta tag); no `eval`; secrets never present in initial HTML; confirmation before any overwrite-apply; parser never throws on garbage input; pure logic modules (`envparse`, `diff`, `redact`, `patch`) shared between browser, CLI, and tests.

## 9. Documentation & testing
README: prerequisites (Node 18+), quickstart, full shortcut map, redaction/threat model, demo script. Tests: `node --test` integration-light coverage of the messy-legacy fixture parsing, drift status computation, fingerprint stability, and patch-apply semantics. Smoke: `npm run smoke` boots the CLI server on an ephemeral port and asserts `/`, `/app.js`, and `/api/seed` respond and that index.html contains the mount node.

## 10. Constraints & non-goals
Not a secrets manager or vault; no writing arbitrary disk files from the UI; no git integration; no multi-user; no frameworks, bundlers, puppeteer, or native builds; never require Electron.

## 11. Acceptance criteria
- [ ] CLI preloads two `--env` files and opens the console window; snapshots persist in localStorage
- [ ] Drift grid shows same/changed/added/removed/empty with masked values + fingerprints
- [ ] Three operator actions work keyboard-only: reveal (`R`), select (`Space`), patch apply (`P` → confirm → `Enter`)
- [ ] Patch apply requires confirmation and writes an AuditEvent; plaintext never renders by default; reveal re-masks on blur
- [ ] `fixtures/legacy-messy.env` (duplicates, `export`, quotes, inline comments, CRLF, malformed lines) parses with warnings, no crash
- [ ] `node --test` and `npm run smoke` pass; `?` cheatsheet and command palette work
- [ ] README demo script and threat model included

## 12. Uniqueness / anti-clone constraints
Must use env-parity domain language (drift, fingerprint, promote, parity, snapshot). Reject: generic file-diff tools, pastebins, todo-style CRUD, plaintext-by-default secret displays, placeholder UIs, and any outbound network call. The fixtures must be realistic environment files (database URLs, API tokens, feature flags), not lorem ipsum.

When done, print `DONE task_7: Env var & secrets sync tool` and start the next task immediately.

---

## Task 08 — Nginx config generator UI
**workdir:** `task_devops_infra_08`
**id:** `devops_infra_08_nginx-config-generator-ui`
**seed (original):** Create an Nginx config generator UI for reverse proxy upstreams, TLS toggles, and downloadable conf.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "visual_diff", "session_shape": "approval_gated", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "java", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "static_html", "persistence": "csv_files", "testing_depth": "smoke_only", "novelty_hook": "deterministic --seed for reproducible runs", "delivery": "notebook_plus_script", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PLATFORM PROMPT — Proxyloom

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
**Proxyloom** is a single-binary Java 17 console that lets a solo developer design, lint, and download production-shaped **Nginx reverse-proxy configurations** without hand-editing `.conf` files. It manages a registry of upstreams (backend app ports on a home-lab VPS), TLS profiles, and server-block "sites", then weaves them into deterministic, downloadable `nginx.conf` output. Everything persists to plain CSV files. The UI is a static-HTML page served by the JDK's built-in HTTP server — no frameworks, no npm, no Docker.

Voice throughout (README, UI copy, comments): a pragmatic solo dev running three side-projects on one box, written first-person and terse.

## 2. Target users & primary jobs-to-be-done
- **Solo dev / home-labber** who self-hosts several apps behind one Nginx instance.
- Jobs: register a new app port → expose it as `app.example.com` → flip TLS on → lint the result → download the conf → keep an audit trail of what changed and when.

## 3. Core requirements / entities (CSV-backed)
- `upstreams.csv`: `name, host, port, scheme, weight, max_fails, health_path, tags`
- `tls_profiles.csv`: `name, mode(off|self-signed|letsencrypt-sim), cert_path, key_path, hsts, redirect_http`
- `sites.csv`: `hostname, listen_port, upstream_ref, tls_profile_ref, websocket, gzip, status(draft|published)`
- `renders.csv`: `render_id, seed, site_hostname, sha1, generated_at`
- `audit.csv`: `timestamp, actor(local), action, target, detail`
All CSV writes are sorted by primary key for byte-stable output.

## 4. Major feature areas
- **Inventory views**: ops-dense tables for upstreams, TLS profiles, sites; status colors documented (draft=amber, published=green, lint-error=red); filter by tag/status/hostname.
- **Detail drawer**: per-site view showing resolved upstream, effective TLS posture, and the rendered server-block snippet.
- **Conf renderer**: deterministic template emitting `upstream{}` + `server{}` blocks, `proxy_pass`, WebSocket upgrade headers, TLS directives per profile, `include`-ready layout; stable ordering (alphabetical) and SHA-1 checksum shown.
- **Linter (simulated `nginx -t`)**: rejects dangling `upstream_ref`, duplicate `listen_port`+`hostname` pairs, TLS `on` with empty cert/key paths, port out of 1–65535, invalid hostname syntax.
- **Actions**: add/edit/delete upstream, create site, toggle TLS profile per site, publish → writes `renders.csv` + audit row; delete blocked with explicit error when referenced by a site.
- **Download**: endpoint returns the full `.conf` as an attachment; also a "copy" view.
- **Read-only mode**: env var `PROXYLOOM_READONLY=1` disables mutating endpoints (HTTP 403) and badges the UI.

## 5. Domain-specific workflows
**Happy path**: `java -jar proxyloom.jar serve --seed 42` seeds fixture CSVs deterministically (names/ports derived from seed; clock fixed to a seed-derived base timestamp) → open `http://localhost:8471` → add upstream `blog:127.0.0.1:9001` → create site `blog.example.com:443` → attach `self-signed` TLS profile → preview render → lint passes → publish → download conf → audit row visible.

**Edge cases**: deleting a referenced upstream → 409 with the referencing site listed; TLS toggle with blank cert path → lint error panel, publish disabled; CSV directory missing → empty-state page with exact `serve --seed` fix hint; read-only mode → mutations rejected politely.

## 6. Data & persistence
CSV files under `./data/` are the sole source of truth; no database. Writes are atomic-ish (write temp + rename). Deterministic `--seed` must make two fresh runs produce byte-identical CSVs, rendered confs, and HTML snapshots.

## 7. UX / API surface
Single `index.html` + vanilla JS fetching small JSON endpoints (`GET/POST/DELETE /api/upstreams`, `/api/sites`, `/api/tls`, `GET /api/render?site=`, `GET /api/download`, `GET /api/audit`). Destructive deletes use a JS confirm dialog naming the target. One failing endpoint must not blank the page — per-panel error states.

## 8. Quality, security, reliability
No shelling out to real `nginx`; the linter is a faithful simulation and must be labeled "simulated nginx -t" in the UI. No external dependencies beyond the JDK. Paths are confined to `./data` and `./out` (no traversal). 2s response budget per endpoint.

## 9. Documentation & testing
- `README.md`: prerequisites (Java 17+ only), quickstart, safety notes, color semantics, first-person solo-dev tone.
- `proxyloom.sh`: one-command script — `seed | serve | render | smoke`.
- `notebooks/demo.ipynb`: bash cells driving the script through inspect → act → lint → download.
- **Smoke test** (`tools/smoke.sh` or JDK-only `SmokeTest.java`): boots server, asserts 200s, performs add-upstream + TLS toggle + publish, asserts linter rejects a dangling-ref site, asserts audit CSV grew. No JUnit downloads.
- **Visual diff** (`tools/visual_diff.sh`): regenerates the deterministic HTML snapshot and a sample rendered conf, diffs against checked-in files under `goldens/`, exits non-zero on drift. Goldens must be reproducible purely via `--seed`.

## 10. Constraints & non-goals
Not a real Nginx controller; no live reloads, no ACME, no multi-server fleets, no auth beyond the trusted-local + read-only flag. No "Hello World" placeholders; every screen must use authentic Nginx vocabulary (`proxy_pass`, `server_name`, `ssl_certificate`, `upstream`, `listen`).

## 11. Acceptance criteria
- [ ] `--seed 42` run twice yields byte-identical CSVs, confs, and HTML snapshot
- [ ] Inventory tables populate from CSV; filter works
- [ ] ≥4 actions work: add upstream, create site, toggle TLS, publish+download
- [ ] Referenced-upstream delete blocked with 409 + message
- [ ] Linter catches dangling ref, duplicate listen/host, TLS-without-cert
- [ ] Download returns a valid-looking `.conf` attachment with checksum shown
- [ ] Read-only mode returns 403 on mutations and badges UI
- [ ] Missing-data-dir empty state with fix hint
- [ ] `tools/smoke.sh` and `tools/visual_diff.sh` both exit 0
- [ ] README + notebook demo succeed as documented

## 12. Uniqueness / anti-clone constraints
Do not emit a generic CRUD or todo app. Required distinctive elements: seed-driven determinism (including fixed clock), CSV-only persistence with sorted keys, the simulated-and-labeled linter, checksum-stamped conf downloads, and the golden-file visual diff. Reject any solution needing Maven/npm downloads or Docker.

When done, print `DONE task_8: Nginx config generator UI` and start the next task immediately.

---

## Task 09 — Backup job orchestrator
**workdir:** `task_devops_infra_09`
**id:** `devops_infra_09_backup-job-orchestrator`
**seed (original):** Build a backup job orchestrator: schedules, destinations, retention, and restore dry-run reports.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "single_shot", "repo_state": "partial_scaffold", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "low", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "devops_ops", "business_domain": "devops_platform", "ui_surface": "api_only", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "export/import round-trip as acceptance", "delivery": "static_build_preview", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PROJECT OBJECTIVE — Holdfast: Backup Job Orchestration Control Plane

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


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

When done, print `DONE task_9: Backup job orchestrator` and start the next task immediately.

---

## Task 10 — Feature flag admin console
**workdir:** `task_devops_infra_10`
**id:** `devops_infra_10_feature-flag-admin-console`
**seed (original):** Create a feature-flag admin console with percentage rollouts, targeting rules, and audit history.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "excel_workbook", "persistence": "json_file", "testing_depth": "unit_plus_smoke", "novelty_hook": "observability: structured logs + simple metrics endpoint", "delivery": "worker_plus_api", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PLATFORM PROMPT — FlagSheet

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

When done, print `DONE task_10: Feature flag admin console` and start the next task immediately.

---
