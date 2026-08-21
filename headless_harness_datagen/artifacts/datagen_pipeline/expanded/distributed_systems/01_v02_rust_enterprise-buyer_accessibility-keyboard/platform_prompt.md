# VARIANT v02_rust_enterprise-buyer_accessibility-keyboard - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `rust`
- **user_persona**: `enterprise_buyer`
- **novelty_hook**: `accessibility_keyboard`
- **ui_surface**: `react_spa`
- **persistence**: `json_file`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `rust`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v02_rust_enterprise-buyer_accessibility-keyboard`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v02_rust_enterprise-buyer_accessibility-keyboard` when demoable.

---

## BASE PRD (honor unless mutated above)

# KILNFIRE — Distributed Firing Scheduler for a Ceramics Collective

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `go`
- **ui_surface:** `game_loop_window`
- **persistence:** `sqlite`
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
Kilnfire is a single-binary, multi-goroutine distributed task queue written in Go that schedules ceramic firing runs ("firings") across a fleet of simulated kiln controllers ("kilns"). Studios submit firings (bisque, glaze, raku) with ramp/soak temperature-curve payloads; a central scheduler leases work to kilns by priority with anti-starvation aging; kilns heartbeat and report progress; failures retry with exponential backoff; unrecoverable runs land on the "cracked shelf" (dead-letter). Ships with a live game-loop TUI "firing board", a REST control plane, SQLite durability, and a chaos **brownout** toggle that kills a kiln mid-run to prove recovery. Written with staff-engineer precision: semantics are stated, not implied.

## 2. Target users & jobs-to-be-done
- **Studio ops lead**: submit rush commissions and watch them complete without babysitting the queue.
- **Studio engineer**: boot the entire fleet with one command, demo failure recovery live, and trust that a restart loses nothing.

## 3. Core entities
- **Firing** (job): id, type (`bisque|glaze|raku`), priority 0–9, curve payload JSON (segments: ramp °C/min, target temp, soak minutes), state, attempts, max_attempts, next_attempt_at, timestamps.
- **FiringAttempt**: id, firing_id, kiln_id, started/finished, outcome, error.
- **Kiln** (worker): id, name, capacity 1, last_heartbeat_at, state (`idle|running|dead`).
- **Lease**: firing_id, kiln_id, expires_at (visibility timeout).
- **CrackedShelf entry** (dead letter): firing snapshot, reason, final error, requeue-able.

State machine: `queued → leased → running → succeeded | failed | retry_wait(→queued) | dead`. Cancel is allowed only from `queued`/`retry_wait`; cancelling a leased firing returns 409.

## 4. Major feature areas
- **Scheduler**: strict priority, FIFO tiebreak, aging (+1 effective priority per 30s queued, capped at 9). Lease = 10s visibility timeout; heartbeat every 2s extends it; 3 missed heartbeats → kiln marked `dead`, its in-flight firing requeued.
- **Kilns**: N goroutines (`--workers`, default 3), one firing at a time; progress ticks advance simulated temperature along the curve; type durations 5–15s so a full demo completes fast.
- **Retries**: delay = `min(1s × 2^(attempt−1) + ±25% jitter, 30s)`; max_attempts 4 (default) → cracked shelf. Delivery guarantee: **at-least-once**; document that re-execution restarts the curve (acceptable for simulated firings) and that attempts are checkpointed.
- **Chaos toggle (required novelty)**: `POST /v1/chaos/brownout` or `--chaos` flag kills one random running kiln mid-run (process stays up). Recoverable path: lease expires, firing is requeued and completed by another kiln, kiln rejoins after ~5s. Event must surface in logs, metrics, and TUI.
- **REST API** (stdlib `net/http`, JSON, `/v1`): `POST /v1/firings`; `GET /v1/firings?state=&type=`; `GET /v1/firings/{id}`; `POST /v1/firings/{id}/cancel`; `GET /v1/kilns`; `GET /v1/deadletters` + `POST /v1/deadletters/{id}/retry`; `GET /v1/metrics` (queue depth, in-flight, succeeded/failed/dead counts, kiln liveness); `POST /v1/chaos/brownout`.
- **Game-loop TUI "firing board"**: stdlib-only ANSI renderer on an update/render tick (~6 fps), no external TUI deps. Shows queue ordered by effective priority, one live temperature gauge + progress % per kiln, cracked shelf, metrics line, last chaos event. Runs in-process; `--no-ui` headless mode for CI.
- **Observability & lifecycle**: `log/slog` JSON lines with `firing_id`, `kiln_id`, `attempt`, `from→to` on every transition. Graceful SIGINT/SIGTERM: stop leasing, let running firings finish up to 10s, otherwise checkpoint + requeue, close DB cleanly, no leaked goroutines.

## 5. Domain workflows
**Happy path**: `go run ./cmd/kilnfire dev` migrates SQLite, boots scheduler + 3 kilns + API on :8080 + TUI, seeds 6 demo firings. A priority-8 glaze rush is leased ahead of an older priority-3 bisque; its gauge climbs to cone temp; it lands `succeeded`; metrics reflect it.
**Edge cases**: brownout mid-run → attempt recorded, firing requeued, another kiln completes it. Retry exhaustion → cracked shelf → manual retry requeues with attempt history preserved. Process restart with queued/running firings → running ones become new attempts, nothing lost.

## 6. Data & persistence
SQLite file (default `./kilnfire.db`), WAL mode, pure-Go driver (`modernc.org/sqlite`) — no CGO. Embedded schema migration at boot. Every state transition is a single UPDATE guarded by expected state (compare-and-swap) so leasing cannot double-assign. Payload cap 64KB. All durable state must survive kill/restart.

## 7. UX / API surface
API-first with consistent error envelope `{error, code}`. Status vocabulary is fixed: `queued, leased, running, retry_wait, succeeded, failed, dead`; kiln states `idle, running, dead`. The TUI is the game-loop window and must tick live without user input.

## 8. Quality, security, reliability
No lost firings on clean shutdown (test-verified). Jitter seed is injectable for deterministic tests. Goroutines owned by one lifecycle supervisor; shutdown asserted leak-free. Structured logs to stdout. No auth (local single-binary tool).

## 9. Documentation & testing
README: one-command dev boot, sample `curl` submit, brownout demo, restart-durability demo, and a semantics section (at-least-once guarantee, lease math, backoff table). **Unit tests**: priority+aging ordering, backoff sequence bounds (1s, 2s, 4s ±jitter, ≤30s cap), lease-expiry requeue, state-machine guards. **Smoke/integration test** (runtime_pass): in-process scheduler + 3 kilns; submit 20 mixed firings including a forced-failure type; assert all reach terminal states within a timeout, ≥2 kilns observed running concurrently, a killed kiln's firing completes elsewhere, and queued firings survive a DB reopen. `go test ./...` must be green.

## 10. Constraints & non-goals
Not Kafka-at-home: no multi-process clustering, no Raft, no external brokers — kilns are goroutines in one binary. No auth, no CGO, no heavy dependencies. Full demo must complete in under 2 minutes.

## 11. Acceptance criteria
- [ ] `go run ./cmd/kilnfire dev` boots API + 3 kilns + ticking TUI and seeds demo firings
- [ ] REST-submitted firing reaches a terminal state; priority 8 overtakes older priority 3
- [ ] Aging boosts a stale low-priority firing
- [ ] Concurrent execution across ≥2 kilns visible in TUI and `/v1/kilns`
- [ ] Brownout kills a kiln mid-run; firing requeued and completed; kiln rejoins
- [ ] Backoff follows 1s/2s/4s ±jitter with 30s cap; max attempts → cracked shelf
- [ ] 3 missed heartbeats marks kiln dead and requeues its firing
- [ ] SIGTERM loses no firings; restart preserves queued state
- [ ] Every transition logged as slog JSON with ids
- [ ] `go test ./...` green, including the multi-kiln integration test

## 12. Uniqueness / anti-clone constraints
Ceramics vocabulary (firing, kiln, cone, ramp/soak, cracked shelf, brownout) is mandatory in API, logs, TUI, and README — no generic "task/job worker" boilerplate naming, no todo-app shapes, no placeholder UI. The firing board must be a live-ticking game-loop render, not a static print. The brownout path must be real, demoable, and recoverable — not a stub or TODO.
