# VARIANT v45_go_student-hacker_feature-flag-gates - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `go`
- **user_persona**: `student_hacker`
- **novelty_hook**: `feature_flag_gates`
- **ui_surface**: `desktop_window`
- **persistence**: `memory_only`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `go`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v45_go_student-hacker_feature-flag-gates`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v45_go_student-hacker_feature-flag-gates` when demoable.

---

## BASE PRD (honor unless mutated above)

# PLATFORM PROMPT — Chalkwire

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `cpp`
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


## 1. Project Request / Product identity

**Chalkwire** is a teacher-paced, live quiz arena for classrooms: the host pushes one
question at a time to every connected slate, students lock in answers against a
countdown bar, and a streak-driven leaderboard updates in real time after each reveal.

- **Audience:** middle/high-school teachers and tutoring-center hosts running
  in-room review sessions (5–32 participants, LAN or single-host internet).
- **Collaboration metaphor:** a **Session** — one host, many players, lockstep rounds.
- **Domain twist (non-tutorial):** *confidence streaks* — correct answers in a row
  multiply points (x1 → x2 → x3 cap); plus a built-in **Chaos Drill** toggle that
  deliberately injects recoverable network faults so the session proves its
  reconnection story live.
- **Stack (locked):** C++17, CMake, raylib-style immediate-mode **game-loop window**
  (60 fps render loop, network on a worker thread), **SQLite** persistence,
  TCP realtime transport (below). No Boost, no web UI, no heavy deps; single-header
  JSON (vendored or FetchContent) is allowed.

## 2. Target users & primary jobs-to-be-done

- **Host (teacher):** create a session from a quiz pack, share the 6-char *chalk
  code*, push/reveal questions, watch live answer counts, flip the Chaos Drill.
- **Player (student):** join by code + display name, answer before the slate
  closes, see own streak and rank, survive a dropped connection without losing score.
- **Spectator:** late joiner; sees lobby/leaderboard, plays from next round.

## 3. Core requirements / entities

Materialize: `QuizPack`, `Question(id, prompt, 4 options, correct_idx, time_limit_s)`,
`Session(id, chalk_code, state: LOBBY|SLATE_OPEN|REVEAL|CLOSED, current_question_idx)`,
`Player(id, display_name, role: HOST|PLAYER|SPECTATOR, resume_token)`,
`PresenceSession(player_id, connected_at, last_heartbeat)`,
`AnswerSubmission(session_id, question_id, player_id, option_idx, latency_ms)`,
`ScoreLedgerEntry(player_id, question_id, base_points, multiplier, total_after)`,
`SessionEvent(seq, type, payload_json)` — append-only, the replay backbone.

## 4. Major feature areas

- **Sessions & membership:** host creates a session; server mints a memorable chalk
  code (e.g. `WREN-42`). Soft cap 32 players; overflow joins as SPECTATOR.
  Roles gate actions: only HOST can push/reveal questions or toggle chaos.
- **Presence & awareness:** heartbeat every 2 s; roster panel shows
  connected/idle/dropped states; in-session activity feed ("Mara locked in",
  "Theo reconnected").
- **Collaborative artifact (the pushed question):** host opens a slate → all clients
  render prompt + 4 options + countdown within one render frame; players submit
  once — **first-answer-locks** (conflict policy: server-authoritative, submissions
  immutable after ACK; last-write-wins only for display-name changes). Host reveals:
  correct option highlighted, per-player deltas animate, leaderboard re-sorts.
- **Scoring engine:** base points by speed tier (full inside first third of window,
  half in second, quarter in final); streak multiplier x1/x2/x3; ledger is
  append-only and recomputed-from-log verifiable.
- **Chaos Drill (required novelty):** server flag `--chaos` or host toggle injects
  one recoverable failure path: random outbound frame delay (0.5–2 s) plus forced
  drop of one client socket every ~20 s. Clients must auto-reconnect with their
  resume token, replay missed `SessionEvent`s, and converge on identical
  leaderboard state. No crash, no lost submission, visible "reconnecting…" banner.

## 5. Domain-specific workflows

**Happy path:** seed loads quiz pack "Intro to Volcanoes" (8 questions) → host
starts session → 3 players join via code → host pushes Q1 → all answer → reveal
shows streaks → final podium screen → session row + ledger persisted.

**Edge cases:** duplicate display names (suffix `-2`); answer after slate closed
(rejected with reason); host disconnect (session pauses, host resume token
reclaims control); reconnect mid-question (client receives current slate +
remaining time); server restart mid-session (reload from SQLite, players re-resume).

## 6. Data & persistence

SQLite file `chalkwire.db` (WAL mode). Tables mirror §3 entities; `SessionEvent`
is the source of truth for replay/resume. Ledger survives server restart; finished
sessions queryable via a `sessions` summary command. Seed script creates the demo
pack and one completed fixture session.

## 7. UX / API surface

- **Game-loop window screens:** Lobby (roster + code), Slate (question, options,
  countdown bar, streak badge), Reveal (animated deltas + top-5 board),
  Podium, plus a persistent connection-status pill (connected/reconnecting/offline).
- **Empty states:** lobby explains "share chalk code WREN-42"; first slate explains
  streak rule in one line.
- **Transport (realtime channel):** persistent TCP, newline-delimited JSON frames:
  `HELLO, JOIN, RESUME, HEARTBEAT, ROSTER, SLATE_OPEN, SUBMIT, SUBMIT_ACK,
  REVEAL, SCORES, EVENT, CHAOS, ERROR`. Server is authoritative for membership,
  timing, scoring, persistence. Client-side prediction limited to local UI;
  leaderboard always renders server values.
- **Modes:** `chalkwire --serve [--headless]` (server only, CI-safe), `chalkwire`
  (windowed client), `chalkwire --bot --name X --code Y --script a,a,b` (scripted
  headless client for tests). One command: `./run.sh` builds, seeds, launches
  server + prints join instructions.

## 8. Quality, security, reliability

Validate codes, names (2–16 chars), option indices; reject malformed frames without
dropping the session. Rate-limit SUBMIT to 1 per question per player. All timing
server-side (client clocks untrusted). Render loop never blocks on network; socket
I/O on a worker thread with a mutex-guarded state queue. `--headless` must require
no display server.

## 9. Documentation & testing

- README: build (CMake ≥3.20, C++17), `./run.sh`, join flow, architecture note
  (threads, event log, replay), chaos drill explanation.
- **Unit tests** (single-header framework or hand-rolled runner): scoring tiers,
  streak multiplier transitions, ledger recompute-from-log equals live total,
  frame codec round-trip, chalk-code collision handling.
- **Smoke test** (`tests/smoke.sh`): launch headless server with `--chaos`, connect
  3 bot clients, kill one mid-slate, resume it, play 3 questions, assert final
  leaderboard JSON matches expected scores and the killed bot's ledger is intact;
  exit 0/1.

## 10. Constraints & non-goals

No accounts/passwords (display name + resume token only), no browser client, no
TLS, no OT/CRDT, no question authoring UI (packs are JSON/SQLite fixtures), no
multi-session sharding. If a CMake/raylib skeleton already exists in the repo,
extend it rather than replacing.

## 11. Acceptance criteria

- [ ] Host + 3 players join one session via chalk code; roles enforced (players
      cannot push/reveal/chaos).
- [ ] Pushed slate renders on all clients without reload; late answers rejected.
- [ ] Reveal broadcasts correct option + per-player deltas; leaderboard order and
      streak multipliers match unit-test-verified scoring rules.
- [ ] Server restart mid-session: players resume via token; ledger intact (SQLite).
- [ ] Chaos Drill: forced client drop auto-recovers; post-replay leaderboard
      identical across all clients; "reconnecting" state visible.
- [ ] 32-player cap overflows to SPECTATOR.
- [ ] `ctest` unit suite green; `tests/smoke.sh` passes fully headless.
- [ ] `./run.sh` is the single dev entry point; README documents realtime flow.

## 12. Uniqueness / anti-clone constraints

This is not a generic "quiz tutorial": no `Room 1`/`User A` placeholders — use
domain language (chalk code, slate, streak, ledger, drill). Scoring must implement
speed tiers × streak multiplier exactly as specified. The Chaos Drill is a
first-class, demonstrable feature, not a stub. UI must be a real rendered game-loop
window with the five named screens, not a console echo of state.
