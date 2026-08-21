# VARIANT v28_python_open-source-maintainer_offline-first - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `python`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `offline_first`
- **ui_surface**: `api_only`
- **persistence**: `csv_files`
- **complexity**: `hard`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `python`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v28_python_open-source-maintainer_offline-first`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v28_python_open-source-maintainer_offline-first` when demoable.

---

## BASE PRD (honor unless mutated above)

# QuayWatch — Mobile-First Docker Triage Console with Audit & Plugin Findings

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `mobile_web`
- **persistence:** `postgres_optional`
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
