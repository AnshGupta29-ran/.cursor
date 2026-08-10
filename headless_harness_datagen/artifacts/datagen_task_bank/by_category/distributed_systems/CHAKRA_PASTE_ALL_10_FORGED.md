# Category batch FORGED: distributed_systems (10/10) — paste into Chakra

Each task is a forged PRD with a **locked dimension mix**. Implementing these under
`harness/chakra/task_distributed_systems_NN/` produces synthetic agent trajectories for stats.

**Playing/demoing alone is NOT datagen** — datagen is the implement session.

## Dimension coverage

| # | complexity | value | language | UI | persistence | verification |
|---|------------|-------|----------|----|-------------|--------------|
| 01 | hard | hard | go | game_loop_window | sqlite | runtime_pass |
| 02 | low | low | rust | cli_tui | json_file | static_pass |
| 03 | medium | medium | python | html_canvas | sqlite | unit_tests |
| 04 | hard | hard | java | react_spa | memory_only | runtime_pass |
| 05 | low | medium | csharp | desktop_window | localstorage | browser_smoke |
| 06 | hard | hard | go | static_html | csv_files | visual_diff |
| 07 | medium | low | typescript | api_only | sqlite | unit_tests |
| 08 | hard | hard | python | excel_workbook | json_file | runtime_pass |
| 09 | medium | medium | rust | mobile_web | postgres_optional | browser_smoke |
| 10 | low | medium | javascript | static_html | memory_only | static_pass |

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

## Task 01 — Distributed task queue (Go)
**workdir:** `task_distributed_systems_01`
**id:** `distributed_systems_01_distributed-task-queue-go`
**seed (original):** Create a distributed task queue framework using Go. Implement a central scheduler, multiple worker nodes, task prioritization, retries with exponential backoff, worker heartbeats, failure detection, persistent job storage using SQLite, and a REST API for submitting and monitoring jobs. Include structured logging, graceful shutdown, concurrency using goroutines, and automated integration tests demonstrating multiple workers processing jobs simultaneously.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "approval_gated", "repo_state": "partial_scaffold", "tool_profile": "mixed", "user_persona": "staff_eng", "complexity": "hard", "value": "hard", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "game_loop_window", "persistence": "sqlite", "testing_depth": "unit_plus_smoke", "novelty_hook": "chaos toggle: inject one recoverable failure path", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# KILNFIRE — Distributed Firing Scheduler for a Ceramics Collective

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

When done, print `DONE task_1: Distributed task queue (Go)` and start the next task immediately.

---

## Task 02 — Priority job scheduler
**workdir:** `task_distributed_systems_02`
**id:** `distributed_systems_02_priority-job-scheduler`
**seed (original):** Build a priority job scheduler with delayed jobs, dead-letter queue, and an admin UI for retry/cancel.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "single_shot", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "low", "language_runtime": "rust", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "cli_tui", "persistence": "json_file", "testing_depth": "smoke_only", "novelty_hook": "domain twist: niche audience + unusual constraint", "delivery": "single_readme_run", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# Umbra — A Dark-Window Job Queue for One-Night Observatory Rigs

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

**Umbra** is a single-binary, single-box priority job scheduler written in **Rust**, built by and for a solo amateur astronomer automating a backyard observatory. Clients submit rig jobs (simulated handlers: `platesolve`, `fitscalibrate`, `dither-seq`, `flatstack`). The twist: **every job carries a "dark window"** — a `not_before` (delayed start) and a `not_after` (sky deadline). A job that misses its window doesn't fail, it **expires** — a first-class terminal state distinct from `failed` and `dead`. Persistence is a single JSON file; the admin surface is an interactive terminal UI (TUI). This is a thin MVP: few files, runnable demo, no polish beyond what proves the semantics.

## 2. Target Users & Jobs-to-be-Done

- **Solo rig operator (you):** "Queue tonight's capture plan, watch it drain from a dashboard, and rescue the flats that dead-lettered before dawn."
- JTBD: submit prioritized jobs with execution windows; observe queue depth and worker liveness at a glance; retry dead jobs; cancel jobs that clouds just ruined.

## 3. Core Entities

- **Job**: id, type, payload (JSON string), priority (0–9, higher first), `not_before`, `not_after`, status, attempts, created_at.
- **Status vocabulary (exact):** `scheduled` (delayed, before window) → `queued` → `leased` → `succeeded` | `failed` (retry pending) | `dead` (DLQ) | `cancelled` | `expired` (window missed).
- **JobAttempt**: job_id, attempt #, worker_id, started/finished, outcome + error message.
- **Worker**: id, heartbeat timestamp, concurrency limit, current job.
- **Lease**: job_id, worker_id, expires_at (visibility timeout).
- **DeadLetter**: job snapshot + final error, retryable from TUI.

## 4. Major Feature Areas

- **Job API (CLI subcommands):** `submit` (type, payload, priority, `--delay-secs`, `--window-secs`), `status <id>`, `list [--state X]`, `cancel <id>` (only when `scheduled`/`queued` — otherwise refused with a clear message).
- **Scheduler:** in-process loop; picks highest-priority `queued` job whose window is open; assigns lease (default 5s visibility timeout). Expired-window jobs transition to `expired`, never re-queued.
- **Workers:** N threads (flag `--workers`, demo uses ≥2); simulated handlers keyed on job type, each doing a tiny deterministic sleep; a payload flag `"fail": true` forces an error (failure injection for the demo). Heartbeat written each loop tick; a worker silent >10s is shown as `STALE` in the TUI.
- **Reliability:** retry with exponential backoff + jitter (base 1s, ×2 per attempt, ±25% jitter), max 3 attempts → `dead`. Delivery semantics: **at-least-once** — document that a crash after handler completion may re-run a job.
- **Admin TUI:** single screen, three panes — job table (state/priority/attempts/window), worker health (heartbeat age, in-flight count), DLQ list. Keys: `r` = retry selected dead job (back to `queued`, attempts reset), `c` = cancel selected job if cancellable, `q` = graceful shutdown.
- **Graceful shutdown:** `q`/Ctrl-C stops leasing, lets in-flight handlers finish (bounded ~2s), requeues unfinished leases, flushes state.json.

## 5. Domain Workflows

**Happy path:** `umbra run --workers 2` in one terminal; `umbra submit platesolve '{"target":"M31"}' --priority 7 --delay-secs 3 --window-secs 60`; job sits `scheduled`, flips to `queued` at window open, gets leased, `succeeded`; attempt history recorded.

**Edge cases that MUST behave:** (a) job whose `not_after` passes while still queued → `expired`; (b) handler error → backoff retries, then `dead` after 3rd attempt; (c) process killed mid-lease → on restart, stale lease recovered, job requeued (attempts preserved); (d) cancel refused on a `leased` job; (e) DLQ retry from TUI succeeds on next scheduler tick.

## 6. Data & Persistence

One file: `state.json` in CWD (or `--state` flag). All entities serialized via serde. Every mutation writes atomically (temp file + rename). On startup the file is loaded; `leased` jobs with dead leases are requeued, `scheduled`/`queued` resume as-is. Schema versioned with a `"v": 1` field. No database, no network.

## 7. UX / API Surface

Single binary `umbra` with subcommands: `run` (scheduler + workers + TUI, the main mode), `submit`, `list`, `status`, `cancel`, `demo` (seeds 6 jobs incl. one failing, one expiring, one delayed — then runs the TUI). Terminal output uses domain terms (`window`, `expired`, `dark window closed`) — never generic "task" boilerplate. Deps kept light: `serde`/`serde_json` required; terminal control via `crossterm` (or hand-rolled ANSI — no heavyweight TUI frameworks required); use `std::time` rather than a date crate if practical.

## 8. Quality, Security & Reliability

No lost jobs on clean shutdown (per at-least-once claim). Backoff math unit-tested. Malformed `state.json` fails loudly with a human-readable error, never silently wiped. No panics on normal error paths (bad payload, missing job id).

## 9. Documentation & Testing

**README (solo-dev first-person voice):** what Umbra is and why dark windows exist; quickstart (`cargo run -- demo`); the demo script explaining the 6 seeded jobs; failure-injection notes ("kill -9 mid-lease, restart, watch recovery"); a short "Delivery guarantees" section. **Testing:** smoke only — a `cargo test` with: backoff schedule correctness, expiry transition, and one multi-thread test where 2 workers drain ≥4 jobs to terminal states.

## 10. Constraints & Non-Goals

- Not a distributed broker: one process, one file, no networking, no consensus.
- No real telescope hardware — handlers are simulated but must persist outcomes.
- No web UI, no auth, no config files beyond CLI flags.

## 11. Acceptance Criteria

- [ ] `cargo run -- demo` runs end-to-end: jobs reach `succeeded`, `dead`, and `expired` visibly in the TUI
- [ ] 2+ workers process jobs concurrently (attempt records show distinct worker ids)
- [ ] Failing job retries with recorded backoff, then lands in DLQ; `r` in TUI re-queues it
- [ ] Killing the process mid-lease and restarting requeues the job without loss
- [ ] `state.json` survives restart; `list` shows prior terminal jobs
- [ ] Cancel refused on non-cancellable states with clear message
- [ ] `cargo test` smoke tests pass
- [ ] README quickstart works from a clean checkout

## 12. Uniqueness / Anti-Clone Constraints

Must keep: observatory dark-window domain, `expired` as a distinct terminal state, JSON-file persistence, terminal TUI admin (not HTTP), Rust. Forbidden: generic "task queue" naming, todo-list framing, placeholder handlers that persist nothing, sleep-only workers with no attempt records.

When done, print `DONE task_2: Priority job scheduler` and start the next task immediately.

---

## Task 03 — Leader election toy cluster
**workdir:** `task_distributed_systems_03`
**id:** `distributed_systems_03_leader-election-toy-cluster`
**seed (original):** Implement a toy leader-election cluster (raft-lite or bully): nodes, heartbeat, failover demo CLI.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "html_canvas", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "must include a live demo mode with sample data", "delivery": "docker_compose_optional", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# GAVEL — Raft-Lite Failover Rehearsal Rig

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

Build **Gavel**, a single-host, multi-threaded Python 3.10+ cluster simulator that runs a raft-lite leader-election protocol and uses the elected leader to issue **epoch-fenced dispatch grants** (monotonic fencing tokens). The product is a *failover rehearsal rig* for engineers who need to demonstrate — not just claim — that a control plane survives leader loss, that terms are monotonic, and that a stale leader's grants are rejected after failover. A live HTML canvas dashboard renders the node ring, heartbeat pulses, and term history in real time. A scripted **demo mode** seeds sample data, runs the cluster, kills the leader on cue, and narrates the failover.

Voice: a staff engineer's internal tool — precise semantics, explicit guarantees, zero hand-waving.

## 2. Target users & primary jobs-to-be-done

- **Staff engineer** rehearsing a failover story before a design review: "show me the cluster elect, lose, and replace a leader in under a minute."
- **Onboarder** learning election mechanics: watch heartbeats, timeouts, and terms change live instead of reading a paper.
- **Tooling engineer** validating fencing-token reasoning: prove a partitioned ex-leader cannot issue valid grants.

## 3. Core requirements / entities

Persisted in **SQLite** (single file, e.g. `gavel.db`):

- **Node** — id, name, role (`follower|candidate|leader`), state (`alive|down`), current term, voted-for, last heartbeat timestamp, concurrency-safe in-process runtime.
- **ElectionEvent** — audit row: term, candidate, votes received, outcome (`won|split|stepped_down`), wall time.
- **HeartbeatEvent** — leader id, term, received-by set, timestamp (sampled/aggregated is fine; don't log every beat).
- **GrantTicket** — fencing token: monotonically increasing `(term, seq)` pair, issued-by node, payload label, status (`active|revoked|rejected_stale`).
- **ClusterMeta** — durable `current_term` / `voted_for` per node so restart restores election state honestly.

Runtime (in-memory OK): election timers, heartbeat scheduler, message-drop flags for simulated partition.

## 4. Major feature areas

- **Raft-lite election**: randomized election timeouts (e.g. 150–300 ms scaled), candidacy, majority vote of alive nodes, split-vote retry with backoff + jitter, step-down on observing a higher term. Log replication of arbitrary entries is **out of scope** — only term/vote/grant state exists.
- **Heartbeat & liveness**: leader broadcasts beats on an interval; followers reset timers on beat; missed beats past timeout trigger election. Dead-node detection must be observable in UI and logs.
- **Fencing-token grants**: only the current-term leader issues `GrantTicket`s with strictly increasing `(term, seq)`. Acceptance rule: a ticket is valid only if its term equals the cluster's durable current term **and** its issuer still holds leadership — a revived ex-leader's tickets are rejected as `rejected_stale`. This is the product's headline guarantee; document it as **at-most-once grant validity per term**.
- **Failure injection**: CLI/API to `kill <node>` (stops its threads, marks down), `revive <node>`, and `partition <node>` (drops inbound messages while keeping it running, so it still issues *stale* grants that must be rejected).
- **Live demo mode**: `python -m gavel demo` boots a 5-node cluster with sample data (named nodes, pre-seeded grant requests like `cron-dispatch`, `cache-warmer`, `report-render`), serves the dashboard, waits ~5s, then kills the leader, narrates re-election, revives the old leader, and shows its stale grant being rejected — all visible on the canvas.
- **Observability**: structured (JSON-line) logs for elections, heartbeats, grants, rejections; a metrics endpoint or CLI `status` showing current term, leader id, alive/dead counts, grants issued/rejected.

## 5. Domain-specific workflows

**Happy path**: start 5 nodes → election completes within ~2 timeout windows → leader heartbeats → client requests 3 grants → all issued with increasing tokens → dashboard shows green ring, pulses, term badge.

**Failover**: kill leader → followers time out → new election at term+1 → new leader resumes grants with higher term → old tickets remain historically valid but no *new* stale tickets accepted.

**Edge cases**: split vote (even cluster / simultaneous candidacy) → backoff and retry until majority; revive ex-leader → it observes higher term and steps down to follower; revive partitioned node that kept "leading" → its grant attempt rejected and logged as `rejected_stale`; full-cluster restart → terms/votes reloaded from SQLite, fresh election proceeds from persisted term (no term regression).

## 6. Data & persistence expectations

SQLite via stdlib `sqlite3`, WAL or busy-timeout to tolerate multi-threaded access. Schema must survive process kill/restart: durable per-node `(current_term, voted_for)` and the full grant ledger. Term is monotonic across restarts — a test must prove a restarted node never votes or leads with a lower term than its persisted value.

## 7. UX / API surface expectations

- **Dashboard**: one HTML page served by the control process using `<canvas>` (vanilla JS, no build step): nodes drawn as a ring; leader highlighted with crown/term badge; animated heartbeat pulses along edges; dead nodes greyed; partitioned nodes hatched; live event ticker (elections, grants, stale rejections); polls a JSON status endpoint every ~500 ms.
- **CLI** (`python -m gavel …`): `start --nodes 5`, `status`, `kill <name>`, `revive <name>`, `partition <name>`, `grant <label>`, `demo`. Human-readable output with correct vocabulary (term, candidate, majority, fencing token).
- Prefer **stdlib only** (`http.server`, `threading`, `sqlite3`, `json`, `unittest`) so the repo runs with zero pip installs.

## 8. Quality, security, and reliability expectations

- Guarantee to state in README: leadership is exclusive per term; fencing tokens are monotonic; delivery semantics for grants = at-most-once validity per term.
- Graceful shutdown: `SIGINT`/CLI stop finishes in-flight grant issuance, flushes SQLite, exits clean with no lost durable state.
- No unbounded threads; election loops must exit on node stop. No external network exposure beyond localhost.

## 9. Documentation & testing expectations

- **README**: architecture sketch (ASCII), semantics/guarantees section, quickstart (`demo` in one command), failure-injection recipes ("kill the leader mid-grant", "partition the leader and watch stale rejection"), schema notes.
- **Unit tests, light** (`unittest`, runnable via `python -m unittest`): majority-win logic, split-vote retry, term monotonicity across simulated restart, stale-grant rejection after failover, heartbeat-timeout triggers candidacy, persistence round-trip of term/vote. ~8–12 focused tests; no heavy fixtures.

## 10. Constraints & non-goals

- Not real Raft: no arbitrary log replication, no snapshots, no membership changes.
- Not multi-process/multi-machine: threads on one host; partitions are simulated message drops, not netem.
- No frameworks required; **docker-compose.yml optional** (single service wrapping `demo`) and must not be needed for the core flow.
- No sleeping-only theater: elections and fencing checks must consult persisted state.

## 11. Acceptance criteria

- [ ] 5-node cluster elects exactly one leader per term; dashboard shows it live on canvas.
- [ ] Killing the leader triggers re-election at term+1 without manual intervention.
- [ ] Grants carry monotonic `(term, seq)` tokens; a revived/partitioned ex-leader's grant is rejected and logged.
- [ ] Restart preserves terms and grant ledger; no term regression.
- [ ] `demo` mode runs the full scripted failover with sample data, unattended.
- [ ] Unit tests pass and cover election, fencing, and persistence.
- [ ] README documents guarantees and failure-injection recipes.

## 12. Uniqueness / anti-clone constraints

This is **not** a generic task queue and not a paper-summary Raft toy: the domain twist is *fencing-token grant issuance as the election's payload*, with stale-leader rejection as the demonstrable guarantee. Ban placeholder UIs, "TODO" semantics, and heartbeat loops that don't drive real elections. Use domain-authentic vocabulary (term, candidacy, majority, fencing token, step-down) throughout code, CLI, and docs.

When done, print `DONE task_3: Leader election toy cluster` and start the next task immediately.

---

## Task 04 — Pub/sub message broker lite
**workdir:** `task_distributed_systems_04`
**id:** `distributed_systems_04_pub-sub-message-broker-lite`
**seed (original):** Create an in-process pub/sub broker with topics, durable subscribers stub, and backpressure stats.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "resume_mid_task", "repo_state": "partial_scaffold", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "java", "artifact_type": "library_sdk", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "react_spa", "persistence": "memory_only", "testing_depth": "unit_plus_smoke", "novelty_hook": "offline-first; no cloud accounts", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PLATFORM PROMPT — HarvestWire

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

I'm a product manager (not an engineer) at a regional food-hub co-op. Our growers shout "what's coming off the field" and our buyers (soup kitchens, grocers, school cafeterias) each want only the categories they care about — without missing anything while their laptop is closed. **HarvestWire** is a small, self-hosted, **offline-first** "harvest ticker": an **in-process pub/sub broker** where growers **publish harvest lots and alerts to topics**, and buyers hold **named durable subscriptions** that keep collecting messages while the buyer is disconnected. No cloud accounts, no external services, no database files — everything lives in broker memory and resets cleanly on restart.

- **Stack (locked):** Java 17+ backend (JDK `com.sun.net.httpserver` or a single light lib like Javalin is fine; keep deps minimal), **React SPA** console (Vite), **in-memory only** persistence.
- **One command:** `./run.sh` (or `make dev`) starts the broker API **and** serves the SPA on a stated port. Must work on a laptop with no network after `npm install`/build.

## 2. Target users & primary jobs-to-be-done

- **Grower (publisher):** post "40 crates of kale, lot #K-118" to `lots.greens` in one action.
- **Buyer (subscriber):** create a durable subscription like `kitchen-riverbend` on `lots.greens`, walk away, come back later, and pull everything missed — newest backlog visible, nothing silently lost (within buffer limits).
- **Hub operator (me):** open the console and *see* which buyers are falling behind (**backpressure**) before they call me angry.

## 3. Core requirements / entities

In-memory domain model, domain-authentic naming:

- **Topic** — name, creation time, per-topic monotonically increasing `sequence`, publish counter, unrouted-drop counter (publish with zero subscribers = dropped + counted).
- **LotMessage** — id, topic, sequence, `key` (e.g., lot code), text payload (≤ 4 KB), `publishedAt`.
- **Subscription** — unique name, topic filter (exact topic or `lots.*` prefix wildcard), **cursor** (last acked sequence per topic), overflow policy, created/last-seen timestamps. Survives subscriber disconnect **in memory** (the "durable stub": durable across client sessions, not across process restarts — documented loudly).
- **Backlog** — per-subscription bounded ring buffer (configurable capacity, default 100) with occupancy stats.
- **StatsSnapshot** — global + per-topic + per-subscription metrics (below).

## 4. Major feature areas

1. **Broker core:** topics auto-created on first publish or subscribe; fan-out copies each message into every matching subscription's backlog; per-topic sequence numbers.
2. **Durable subscriptions (stub):** named subscriptions persist in broker memory after the consumer disconnects; a new consumer attaching with the same name **resumes from the cursor**. Explicit `ack` advances the cursor; `nack` or ack-timeout (default 30 s) triggers **redelivery** (at-least-once — state this in the README).
3. **Backpressure:** per-subscription bounded backlog with selectable overflow policy: `DROP_OLDEST` (default), `DROP_NEW`, or `REJECT_PUBLISH` (publish call returns an error for that topic when any matching subscription is full). Every drop/reject is counted.
4. **Stats API:** queue depth (pending per subscription), lag (newest topic sequence − cursor), buffer occupancy %, dropped count, redelivered count, oldest-pending-message age, per-topic publish totals.
5. **React console ("Packing Shed Board"):** topic list with publish form; subscription inspector with lag gauges and overflow-policy badges; live message tail per subscription (poll every 2 s — no websockets required); stats strip (totals: published / delivered / acked / dropped).
6. **Clean shutdown:** `SIGINT`/stop endpoint flushes nothing to disk (memory-only is explicit) but logs a final stats summary.

## 5. Domain-specific workflows

**Happy path:** create subscription `kitchen-riverbend` on `lots.greens` → publish 3 lots → `POST /poll` returns 3 → `ack` all → lag = 0 everywhere.

**Edge cases to handle and document:**
- Publish to a topic with **no subscriptions** → message unrouted, counted in stats.
- Subscriber disconnects mid-batch, reconnects later with same name → resumes from cursor, no duplicates *after* ack, redelivery of un-acked.
- Backlog overflow under `DROP_OLDEST` → oldest evicted, cursor auto-advances past evicted messages, drop counter increments; SPA badge shows "lost 12 to overflow".
- Publish with `REJECT_PUBLISH` and a full subscriber → HTTP 429-style error naming the blocking subscription.
- Wildcard `lots.*` receives `lots.greens` + `lots.orchard` but not `alerts.frost`.

## 6. Data & persistence expectations

Memory only. All state in broker data structures; **no files, no SQLite, no disk writes**. README must state plainly: restart = clean slate, and "durable" means durable across *client* disconnects within one broker run. Config (buffer sizes, ack timeout, default policy) via env vars or CLI flags with sane defaults.

## 7. UX / API surface expectations

REST JSON API (document each route in README):

- `POST /topics/{topic}/publish` — body `{key, payload}` → `{sequence}` or overflow error.
- `PUT /subscriptions` — `{name, topicFilter, overflowPolicy?, capacity?}`; `GET /subscriptions`; `DELETE /subscriptions/{name}`.
- `POST /subscriptions/{name}/poll?max=N` → batch of messages with `deliveryId`.
- `POST /subscriptions/{name}/ack` / `/nack` — by `deliveryId`.
- `GET /stats` — global + per-topic + per-subscription snapshot.

SPA served at `/`; status vocabulary consistent everywhere: `pending`, `delivered-awaiting-ack`, `acked`, `dropped`.

## 8. Quality, security, and reliability expectations

At-least-once delivery per subscription; no message loss *within* declared limits (capacity, overflow policy). Thread-safe broker (concurrent publishers/pollers). Payload cap 4 KB; reject oversized with clear error. No auth (local tool) — say so. Structured log lines for publish/ack/drop/redeliver/shutdown.

## 9. Documentation & testing expectations

- **README:** one-command start, copy-paste `curl` demo (subscribe → publish → poll → ack → check stats), "close the buyer and come back" durability demo, overflow demo, delivery-guarantees section, restart-resets warning.
- **Unit tests:** fan-out, wildcard matching, cursor resume, ack/nack + redelivery, each overflow policy, sequence monotonicity.
- **Smoke test** (`./smoke.sh` or test class): boot server, run the happy-path + one overflow scenario via HTTP, assert stats numbers, exit non-zero on failure. Runtime verification: server boots and smoke passes.

## 10. Constraints & non-goals

No Kafka-isms, no clustering, no persistence to disk, no WebSockets, no auth, no cloud SDKs, no Docker requirement, no sleeping-only fake consumers.

## 11. Acceptance criteria

- [ ] `./run.sh` brings up API + SPA with no other manual steps (post-install).
- [ ] Publish fans out to ≥2 matching subscriptions independently.
- [ ] Subscriber disconnect → reconnect with same name resumes without re-acking old messages.
- [ ] Un-acked messages are redelivered after nack/timeout; acked ones never are.
- [ ] All three overflow policies behave per spec and increment drop counters.
- [ ] `/stats` lag/depth/occupancy match a scripted publish/ack sequence exactly.
- [ ] SPA shows topics, subscriptions, live tail, and lag gauges updating without manual refresh.
- [ ] Unit tests + smoke test pass; README demo reproducible by a non-engineer.

## 12. Uniqueness / anti-clone constraints

This is **HarvestWire**, a food-hub harvest ticker — not a generic task queue or chat demo. Use domain terms (lot, crate, topic like `lots.orchard`, subscription like `kitchen-riverbend`) throughout code, UI, and README. No lorem ipsum, no "Todo", no placeholder panels; seed the demo script with realistic produce lots and a frost alert.

When done, print `DONE task_4: Pub/sub message broker lite` and start the next task immediately.

---

## Task 05 — MapReduce wordcount lab
**workdir:** `task_distributed_systems_05`
**id:** `distributed_systems_05_mapreduce-wordcount-lab`
**seed (original):** Build a mini MapReduce wordcount: split files, map workers, shuffle, reduce, and merge output.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "multi_turn_repair", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "low", "value": "medium", "language_runtime": "csharp", "artifact_type": "cli_tool", "task_family": "data_wrangling", "business_domain": "data_analytics", "ui_surface": "desktop_window", "persistence": "localstorage", "testing_depth": "integration_light", "novelty_hook": "accessibility-first keyboard UX", "delivery": "cli_entry_plus_ui", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PlainTally — Keyboard-First Mini MapReduce Word-Frequency Auditor

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
PlainTally is a single-machine C# (.NET 8) miniature MapReduce engine for enterprise content-governance teams. It ingests a folder of `.txt`/`.md` policy documents, splits them into chunks, runs concurrent map workers that tokenize words, shuffles by hash partition, reduces to global term frequencies, and merges a ranked report with CSV export. Differentiator: an accessibility-first **desktop window** where the entire pipeline is operable and perceivable by keyboard alone — procurement-ready for WCAG 2.2 AA / Section 508 programs. Dual delivery: CLI entry (`plaintally run <folder>`) for scripted audits, and a desktop UI for analysts. Thin MVP: few files, minimal polish, runnable demo.

## 2. Target users & jobs-to-be-done
- **Compliance/content-governance lead (enterprise buyer):** prove plain-language adherence across a corpus without sending data to any cloud service — everything runs locally.
- **Accessibility-minded analyst:** run an audit, inspect dead-lettered chunks, and export results using keyboard + screen reader only.
Jobs: "Audit this folder into a ranked term/jargon frequency report." "Show which chunks failed and why." "Re-run after fixes, keeping an auditable local history."

## 3. Core requirements / entities
- `AuditJob`: id, source folder, status vocabulary: `Queued → Splitting → Mapping → Shuffling → Reducing → Merging → Succeeded | Failed | PartialWithDeadLetters | Cancelled`.
- `ChunkTask`: map unit (file + byte range), attempts, lease with visibility timeout (~5s).
- `TaskAttempt`: worker id, start/end, outcome, error.
- `Worker`: id, heartbeat timestamp, concurrency cap (default 2; demo must show ≥2), state `Idle|Busy|Lost`.
- `ShufflePartition`: hash bucket of word → partial counts (R=4).
- `DeadLetter`: chunk that exhausted attempts, with last error.
- `JobRecord`: persisted summary (top-N terms, dead letters, counts) in browser localStorage.
Engine state is in-memory during a run; durable artifacts live in localStorage (§6).

## 4. Major feature areas
- **Splitter:** enumerate files; split into ~64KB chunks aligned to line boundaries (never mid-line).
- **Scheduler:** priority FIFO; assigns tasks to workers; stale-heartbeat tasks are re-leased after the visibility timeout; per-worker concurrency limit.
- **Map workers:** thread-pool tasks; tokenize (lowercase, strip punctuation), emit `(word,1)`; heartbeat every 500ms; liveness detection marks workers `Lost`.
- **Shuffle/reduce:** hash partitions; reducers sum counts. Delivery claim (document): **at-least-once** task execution with idempotent, commutative aggregation.
- **Reliability:** exponential backoff + jitter (base 200ms, ×2, ±50% jitter), max 3 attempts → DeadLetter; job ends `PartialWithDeadLetters` if DL non-empty.
- **Merge:** deterministic sort (count desc, word asc); export top-1000 CSV.
- **Chaos toggle:** injects ~25% random map-task failures to demonstrate retries/DLQ.
- **Observability:** metrics strip (queue depth, in-flight, succeeded, failed, retried, dead-lettered); structured JSON-lines log pane; graceful stop finishes the current chunk then requeues.
- **CLI:** `plaintally run <folder> [--chaos] [--workers N]` prints JSON summary + writes CSV; `plaintally ui` opens the window.

## 5. Domain-specific workflows
**Happy path:** open window → Ctrl+O picks folder → Ctrl+Enter starts → live region announces each stage → results grid receives focus → arrow keys browse terms → Enter shows per-document counts → Ctrl+E exports CSV.
**Edge cases:** empty folder (clear empty state); unreadable/binary file (chunk retries → dead-letter, job still merges surviving data); worker killed mid-task (lease expiry requeues, nothing lost); duplicate execution after retry (counts stay correct — verify against fixture with known counts); Stop mid-run (in-flight chunk completes, rest requeue, job recorded `Cancelled`).

## 6. Data & persistence expectations
localStorage keys (prefix `plaintally.`): `jobs` (last 20 JobRecords incl. dead letters), `lastReport` (merged top-N + CSV text), `prefs` (contrast, reduced motion, shortcuts dismissed). Closing/reopening the window must restore history, last report, and preferences. Include a "Clear local history" action. No servers, databases, or cloud.

## 7. UX / API surface expectations
Desktop window — suggest Photino.NET hosting one `web/index.html`; **the same file must open standalone in a browser with demo data** so it passes a browser smoke test without the backend. Keyboard-complete:
- Logical tab order, always-visible focus ring, skip-to-results link.
- Results as a real grid: arrow-key navigation, Enter opens term detail.
- `aria-live="polite"` announcer for stage/metric changes; progressbar roles on stage meters.
- Shortcut palette on `?` (Ctrl+O, Ctrl+Enter, Ctrl+E, Ctrl+L logs, Ctrl+Shift+X chaos).
- Honor `prefers-reduced-motion`; persisted high-contrast toggle; ≥4.5:1 text contrast.
- Domain vocabulary on screen: chunks, partitions, leases, dead letters — never generic "items".

## 8. Quality, security, reliability
Local-only; path validation confines reads to the selected folder; skip files >10MB with notice. No lost chunks on clean stop; retries never double-count (integration-verified). Structured logs; no PII leaves the machine.

## 9. Documentation & testing
README: .NET 8 install, CLI demo, UI demo, failure-injection walkthrough (enable chaos / kill a worker → observe backoff + DLQ), delivery-semantics section (at-least-once + idempotent reduce), full keyboard map. Tests (light integration, xUnit): (a) ≥2 workers process a fixture corpus and merged counts match a hand-computed baseline; (b) a failing worker produces backoff bookkeeping and dead-letter after max attempts. Browser smoke checklist: open `index.html` standalone; verify render, live-region announcements on demo data, and a complete keyboard loop.

## 10. Constraints & non-goals
Not Hadoop/Spark; single machine, simulated distribution via threads; no network RPC, external services, or heavy dependencies. Few files: one small engine project, one UI host, one HTML page, one test file. No sleeping-only fake workers — tasks must do real tokenization.

## 11. Acceptance criteria
- [ ] CLI audits a folder and prints correct JSON + CSV.
- [ ] Desktop window runs the full pipeline; ≥2 workers visibly process concurrently.
- [ ] Chaos mode yields retries with backoff+jitter; exhausted tasks land in dead-letter; job reports `PartialWithDeadLetters`.
- [ ] Worker heartbeat loss is detected; its chunk is re-leased without loss.
- [ ] Window restart restores history/report/prefs from localStorage.
- [ ] Every UI action is keyboard-reachable; stage changes announced via live region.
- [ ] Integration tests pass; `index.html` passes standalone browser smoke.
- [ ] README demo + semantics section complete.

## 12. Uniqueness / anti-clone constraints
Forbidden: generic todo/CRUD scaffolding, "hello queue" boilerplate, placeholder tables, lorem-ipsum corpora. Must use MapReduce/audit terminology (chunks, shuffle partitions, leases, dead letters, jargon density). Fixture corpus must be plausible policy documents (`travel-policy.md`, `security-handbook.txt`, …) with a hand-computable word baseline. Accessibility-first keyboard UX is a hard feature, not a nicety.

When done, print `DONE task_5: MapReduce wordcount lab` and start the next task immediately.

---

## Task 06 — Distributed lock service
**workdir:** `task_distributed_systems_06`
**id:** `distributed_systems_06_distributed-lock-service`
**seed (original):** Implement a distributed lock service API with TTL, fencing tokens, and contention tests.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "visual_diff", "session_shape": "approval_gated", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "static_html", "persistence": "csv_files", "testing_depth": "smoke_only", "novelty_hook": "deterministic --seed for reproducible runs", "delivery": "notebook_plus_script", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# DistributedLockService — Distributed lock service

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **DistributedLockService** for category `distributed_systems`. Seed intent (honor this product, do not genericize away):

> Implement a distributed lock service API with TTL, fencing tokens, and contention tests.

Artifact type: `backend_api`. Novelty hook: deterministic --seed for reproducible runs. Delivery: `notebook_plus_script`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`csv_files`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **hard**:
- Richer entity model, edge cases, and verification from acceptance list
- Multi-view or multi-endpoint surface matching ui_surface
- Stronger README + smoke/unit coverage as locked
- Higher visual fidelity when UI is not api_only/cli_tui

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`csv_files` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`static_html`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (hard fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`smoke_only` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `smoke_only` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **hard** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_6: Distributed lock service` and start the next task immediately.

---

## Task 07 — Sharded key-value store
**workdir:** `task_distributed_systems_07`
**id:** `distributed_systems_07_sharded-key-value-store`
**seed (original):** Create a sharded key-value store demo with consistent hashing, get/put, and rebalance command.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "single_shot", "repo_state": "partial_scaffold", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "low", "language_runtime": "typescript", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "api_only", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "export/import round-trip as acceptance", "delivery": "static_build_preview", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# ShardedKeyValue — Sharded key-value store

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

When done, print `DONE task_7: Sharded key-value store` and start the next task immediately.

---

## Task 08 — Workflow saga orchestrator
**workdir:** `task_distributed_systems_08`
**id:** `distributed_systems_08_workflow-saga-orchestrator`
**seed (original):** Build a saga/workflow orchestrator for multi-step jobs with compensations on failure.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "finance_fintech", "ui_surface": "excel_workbook", "persistence": "json_file", "testing_depth": "unit_plus_smoke", "novelty_hook": "observability: structured logs + simple metrics endpoint", "delivery": "worker_plus_api", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# WorkflowSagaOrchestrator — Workflow saga orchestrator

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **WorkflowSagaOrchestrator** for category `distributed_systems`. Seed intent (honor this product, do not genericize away):

> Build a saga/workflow orchestrator for multi-step jobs with compensations on failure.

Artifact type: `backend_api`. Novelty hook: observability: structured logs + simple metrics endpoint. Delivery: `worker_plus_api`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`json_file`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **hard**:
- Richer entity model, edge cases, and verification from acceptance list
- Multi-view or multi-endpoint surface matching ui_surface
- Stronger README + smoke/unit coverage as locked
- Higher visual fidelity when UI is not api_only/cli_tui

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`json_file` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`excel_workbook`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (hard fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`unit_plus_smoke` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `unit_plus_smoke` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **hard** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_8: Workflow saga orchestrator` and start the next task immediately.

---

## Task 09 — Batch fan-out email workers
**workdir:** `task_distributed_systems_09`
**id:** `distributed_systems_09_batch-fan-out-email-workers`
**seed (original):** Create a fan-out email sending simulator: enqueue campaigns, workers send stubs, track delivery states.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "resume_mid_task", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "medium", "value": "medium", "language_runtime": "rust", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "media_cms", "ui_surface": "mobile_web", "persistence": "postgres_optional", "testing_depth": "browser_smoke", "novelty_hook": "plugin/extension hook (one stub plugin)", "delivery": "monorepo_client_server", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# BatchFanOut — Batch fan-out email workers

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
Build **BatchFanOut** for category `distributed_systems`. Seed intent (honor this product, do not genericize away):

> Create a fan-out email sending simulator: enqueue campaigns, workers send stubs, track delivery states.

Artifact type: `backend_api`. Novelty hook: plugin/extension hook (one stub plugin). Delivery: `monorepo_client_server`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`postgres_optional`.
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
Use persistence=`postgres_optional` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`mobile_web`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (medium fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`browser_smoke` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `browser_smoke` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **medium** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_9: Batch fan-out email workers` and start the next task immediately.

---

## Task 10 — Clock skew demo + NTP stub
**workdir:** `task_distributed_systems_10`
**id:** `distributed_systems_10_clock-skew-demo-ntp-stub`
**seed (original):** Build a multi-node clock skew demo showing logical clocks/vector clocks for event ordering.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "javascript", "artifact_type": "cli_tool", "task_family": "analysis_reason", "business_domain": "devops_platform", "ui_surface": "static_html", "persistence": "memory_only", "testing_depth": "smoke_only", "novelty_hook": "multi-theme or multi-difficulty presets", "delivery": "library_plus_demo_app", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# ClockSkewDemo — Clock skew demo + NTP stub

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **ClockSkewDemo** for category `distributed_systems`. Seed intent (honor this product, do not genericize away):

> Build a multi-node clock skew demo showing logical clocks/vector clocks for event ordering.

Artifact type: `cli_tool`. Novelty hook: multi-theme or multi-difficulty presets. Delivery: `library_plus_demo_app`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`memory_only`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **low**:
- Thin file count; prefer stdlib / minimal deps
- One primary happy path + 2–3 edge cases
- Visuals: plain CSS, no animation libraries, no heavy chart frameworks

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`memory_only` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`static_html`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (low fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`smoke_only` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `smoke_only` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **low** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_10: Clock skew demo + NTP stub` and start the next task immediately.

---
