# VARIANT v11_csharp_solo-founder_accessibility-keyboard - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `csharp`
- **user_persona**: `solo_founder`
- **novelty_hook**: `accessibility_keyboard`
- **ui_surface**: `cli_tui`
- **persistence**: `sqlite`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `csharp`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v11_csharp_solo-founder_accessibility-keyboard`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v11_csharp_solo-founder_accessibility-keyboard` when demoable.

---

## BASE PRD (honor unless mutated above)

# Umbra — A Dark-Window Job Queue for One-Night Observatory Rigs

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `rust`
- **ui_surface:** `cli_tui`
- **persistence:** `json_file`
- **complexity:** `low`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.


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
