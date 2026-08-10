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
