# Category batch FORGED: collaborative_realtime (10/10) — paste into Chakra

Each task is a forged PRD with a **locked dimension mix**. Implementing these under
`harness/chakra/task_collaborative_realtime_NN/` produces synthetic agent trajectories for stats.

**Playing/demoing alone is NOT datagen** — datagen is the implement session.

## Dimension coverage

| # | complexity | value | language | UI | persistence | verification |
|---|------------|-------|----------|----|-------------|--------------|
| 01 | medium | low | python | api_only | sqlite | unit_tests |
| 02 | hard | hard | typescript | excel_workbook | json_file | runtime_pass |
| 03 | medium | medium | javascript | mobile_web | postgres_optional | browser_smoke |
| 04 | low | medium | csharp | static_html | memory_only | static_pass |
| 05 | hard | hard | cpp | game_loop_window | sqlite | runtime_pass |
| 06 | low | low | rust | cli_tui | json_file | static_pass |
| 07 | medium | medium | go | html_canvas | sqlite | unit_tests |
| 08 | hard | hard | java | react_spa | memory_only | runtime_pass |
| 09 | low | medium | typescript | desktop_window | localstorage | browser_smoke |
| 10 | hard | hard | python | static_html | csv_files | visual_diff |

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

## Task 01 — Slack-style team chat
**workdir:** `task_collaborative_realtime_01`
**id:** `collaborative_realtime_01_slack-style-team-chat`
**seed (original):** Build a Slack-style team chat application with channels, private messaging, notifications, and file sharing.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "single_shot", "repo_state": "partial_scaffold", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "low", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "productivity_collab", "modality": "text_code", "ui_surface": "api_only", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "export/import round-trip as acceptance", "delivery": "static_build_preview"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints Build-first: implement from PRD; forbid WebSearch/WebFetch and repo-wide fishing; code > research **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# BridgeLine — Incident-Bridge Team Chat (API-only, Python + SQLite)

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

**BridgeLine** is a self-hosted team chat **API service** for on-call engineering crews. Channels double as *incident bridges*: any message can be flagged as a **timeline marker** (e.g. `mitigation_applied`, `escalated`, `resolved`), and the entire workspace can be exported to a portable JSON archive and re-imported into a fresh database — producing postmortem-ready records and reproducible environments.

One-sentence pitch: *Slack-style chat primitives, purpose-built for incident response, with a verifiable export/import round-trip as a first-class feature.*

## 2. Target users & jobs-to-be-done

- **Incident commanders** — spin up a bridge mid-page, keep a durable, ordered timeline.
- **Responders** — share log bundles/screenshots, get pinged only on relevant keywords.
- **Staff+ engineers** — archive the bridge afterward; re-import into a scratch instance to rebuild context or test automation.

## 3. Core requirements / entities

Materialize these (names may vary, substance may not):

- **User** — display name, opaque API token.
- **Workspace** — named tenant; soft cap of 50 members.
- **Membership** — role: `owner` | `member` | `guest`. Guests are read-only, joined to specific channels, and **cannot upload files or create channels**.
- **Channel** — kind: `public` | `private` | `dm`. DMs are deterministic per user-pair (re-requesting returns the same channel).
- **Message** — body, author, channel, `seq` (from event log), soft-delete, `edited_at` (last-write-wins).
- **Marker** — type + message reference; any non-guest may mark/unmark.
- **Attachment** — sha256-named blob on disk + metadata row (uploader, size, content type).
- **KeywordWatch** — per-user substring list driving notifications.
- **Notification** — mention or keyword hit; ack-able.
- **Event** — append-only log, monotonic `seq` per workspace; backbone for realtime replay and unread counts (`last_read_seq`).
- **Invite** — code, role granted, expiry, single-use optional.

## 4. Major feature areas

1. **Workspaces & membership** — create workspace (creator = owner); invite codes with role + expiry; join by code; role checks on every restricted mutation.
2. **Channels & DMs** — public channels joinable by members; private by owner/member invite; DM creation idempotent; unread counts derived from `last_read_seq` vs channel max `seq`.
3. **Messaging & markers** — post / edit (LWW) / soft-delete; history paginated by `seq` (cursor, not offset); markers listable per channel for postmortem timelines.
4. **Notifications** — `@mention` and keyword-watch matches create one notification **per user per message** (dedupe overlapping rules); list + ack endpoints; pushed over the realtime channel.
5. **File sharing** — `POST /channels/{id}/attachments` (≤10 MB, 413 over), stored under `data/uploads/<sha256>`, download requires membership, guests get 403 on upload.
6. **Realtime transport** — WebSocket `/ws?token=…`. Presence (`online`/`idle` after 30 s without heartbeat/`offline`). Every mutation appends an Event; server fans out. Reconnect contract: `GET /workspaces/{id}/events?after_seq=N` replays missed events in order; clients dedupe by `seq` — duplicates after a blip are expected and harmless.
7. **Export / import (signature feature)** — `GET /workspaces/{id}/export` streams a canonical JSON archive (all entities incl. markers, notifications, and attachments base64-embedded; sorted keys, stable IDs preserved). `POST /import` loads an archive into an **empty** database (409 otherwise).

## 5. Domain workflows

**Happy path:** owner creates workspace `sre-oncall` → invites responders → creates `#inc-2417-cache-stampede` → responders chat over WS, one uploads a pcap excerpt → commander marks two messages (`mitigation_applied`, `resolved`) → exports archive for the postmortem.

**Edge cases that must behave:** guest upload → 403; import into non-empty DB → 409; expired invite → 410; reconnect with stale `after_seq` → full ordered replay, no gaps, no dupes visible after client dedupe; edit race → last write wins, `edited_at` set; soft-deleted messages excluded from history but retained in export with tombstone flag.

## 6. Data & persistence

SQLite at `data/bridgeline.db`, WAL mode, single-writer discipline, parameterized queries only. Event log is never purged in MVP. Export must be **deterministic**: `export → import into fresh DB → export` yields byte-identical JSON. That equality is an acceptance test, not a hope.

## 7. API surface expectations

REST under `/api/v1` + the WebSocket endpoint. Auth via `X-BridgeLine-Token` header. Uniform error envelope `{ "error": { "code", "message" } }` with correct status codes (403 role, 409 conflict, 413 size, 422 validation). OpenAPI schema auto-generated. **Static build preview:** a `make preview` (or equivalent script) that emits `dist/` containing the frozen `openapi.json` plus a single dependency-free `index.html` smoke console (fetch-based: create workspace, post message, list events). No SPA framework, no other frontend.

## 8. Quality, security, reliability

Rate-limit message posting (e.g. 10/5 s per user → 429). Constant-time token comparison. Validate all payloads. If the WS drops, REST remains fully functional — document that degradation path.

## 9. Documentation & testing

- `README.md`: setup, run, curl walkthrough of the happy path, preview build.
- `ARCHITECTURE.md`: realtime fan-out, reconnect/replay contract, export format spec.
- `python -m app.seed`: creates `sre-oncall` with `#inc-2417-cache-stampede`, three users across all roles, markers, one attachment.
- **pytest (light):** (a) role enforcement incl. guest upload 403, (b) message → event seq ordering + `after_seq` replay, (c) keyword/mention notification dedupe, (d) **export→import→export byte equality**.

## 10. Constraints & non-goals

Python 3.10+; prefer FastAPI or Flask + stdlib sqlite3; light local deps only. No browser UI beyond the smoke page, no E2E/browser tests, no threading/replies, no full-text search engine (`LIKE` fine), no CRDT/OT, no multi-process presence.

## 11. Acceptance criteria

- [ ] Two users join one workspace via invite and see each other's messages over WS without polling.
- [ ] Server restart restores full state from SQLite.
- [ ] At least one guest-restricted action is enforced and tested.
- [ ] Reconnect with `after_seq` replays exactly the missed events, in order.
- [ ] Export/import round-trip produces byte-identical archives (tested).
- [ ] All pytest tests pass; README steps run the stack; `dist/` preview builds.

## 12. Uniqueness / anti-clone constraints

This is **not** a Socket.IO-chat tutorial with new labels. Incident-domain language is mandatory (bridges, markers, postmortem archive) — seed data like `Room 1`/`User A` is forbidden. Timeline markers and the verifiable archive round-trip are the signature features; dropping either fails the run. The deliverable is an API service with a static preview, not a chat web app.

When done, print `DONE task_1: Slack-style team chat` and start the next task immediately.

---

## Task 02 — Multiplayer kanban board live sync
**workdir:** `task_collaborative_realtime_02`
**id:** `collaborative_realtime_02_multiplayer-kanban-board-live-sync`
**seed (original):** Create a multiplayer kanban board where cards and columns sync in real time across users with presence indicators, conflict-safe moves, and room-based boards.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "productivity_collab", "ui_surface": "excel_workbook", "persistence": "json_file", "testing_depth": "unit_plus_smoke", "novelty_hook": "observability: structured logs + simple metrics endpoint", "delivery": "worker_plus_api", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths Build-first still applies: no online research loops; deepen the product with Write/Edit, not Explore agents **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# SheetFlow — Live Job-Board Workbooks for Print & Sign Shops

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

**Product:** SheetFlow
**Pitch (from the PM, non-technical):** Small print and sign shops run their whole day out of one shared spreadsheet — one tab per production stage, one row per job. That file locks, goes stale, and nobody knows who’s editing it. SheetFlow is that same workbook, but multiplayer: every change shows up on everyone’s screen instantly, and the system referees when two people touch the same job at once.

- **Audience:** production coordinators and shop-floor crew (5–20 people per shop).
- **Metaphor:** a *room* = one workbook; each production stage = a sheet tab; each job = a row.
- **Domain twist:** Excel-co-authoring-style presence (each person’s selected row glows in their color) plus server-refereed moves — two people dragging the same job can never corrupt the board.

## 2. Target users & jobs-to-be-done

- **Coordinator:** creates the shop board, shares the room code, watches work flow all day.
- **Crew member:** joins with just a name; moves a job to the next stage the moment it’s done; flags a job as *rush*.
- **Owner:** read-only oversight from the office without touching anything.

## 3. Core requirements / entities

- `Room` — id, shop name, 6-character join code, stage order, createdAt
- `Stage` — id, name, position (rendered as a sheet tab; defaults: Intake, Prepress, On Press, Finishing, Pickup)
- `JobTicket` — id, auto job number (`JB-1042`), client, title, dueDate, rush flag, stageId, position, version, updatedBy
- `Member` — id, displayName, role (`owner` | `editor` | `viewer`), assigned color
- `PresenceSession` — memberId, selectedJobId, idle, lastSeen
- `BoardEvent` — seq, roomId, type, payload, actor, timestamp (in-room history)

## 4. Major feature areas

**A. Workbook UI (Vite + React + TypeScript):** bottom sheet tabs = stages with job counts; active tab shows a grid with column letters and row numbers; each row is a JobTicket (Job #, Client, Job, Due, Rush). In-cell editing via double-click/Enter; an Excel-style formula bar at top edits the selected row. Move a job by dragging its row onto another tab, or via a “Move ▸” row menu. Owners can add/rename stages; deleting a job asks for confirmation.

**B. Realtime (WebSocket, server-authoritative):** all mutations go to the server, which assigns a per-room sequence number and broadcasts ordered events. Reconnecting clients send their last seen seq; server replays missed events or sends a fresh snapshot.

**C. Presence:** color-assigned avatars in the top bar; a member’s selected row gets a colored border + name chip; members go “idle” after 60s and fade on disconnect.

**D. Conflict policy (pick and implement this one):** the server is the referee. Every ticket carries a version; edits/moves include it. Stale requests are rejected and that client resyncs: the row animates to its official position with a toast like *“Sam moved JB-1042 first — board updated.”* Last writer (by server arrival) wins; both screens must end identical.

**E. Roles:** owner (rename board/stages, clear board), editor (all job operations), viewer (read-only). Enforced server-side, not just hidden buttons.

**F. Activity panel:** slide-over listing the last 50 events (“Priya moved JB-1040 to On Press”).

**G. Observability:** both processes emit single-line JSON logs (`ts, level, event, roomId, memberId, ms`) to stdout. `GET /api/metrics` returns `{ uptimeSec, activeRooms, liveConnections, movesTotal, editsTotal, conflictsTotal, avgBroadcastMs }`.

## 5. Domain workflows

**Happy path:** owner creates “Sunrise Signs & Print” → gets code `K7P2QX` → crew joins by name → coordinator adds “500 tri-fold menus — Rosa’s Cantina” → press operator drags it to *On Press* → every screen updates within a second.

**Edge cases:** simultaneous move of the same job (server order wins, loser resyncs with toast, `conflictsTotal` increments, no ghost rows) · network drop (banner “Reconnecting…”, auto-reconnect, missed events replayed) · viewer attempts a drag (controls disabled + server rejects) · job titles may duplicate but job numbers are unique and auto-increment per room · server restart (board restores from disk; clients resync) · empty stage shows a teaching empty state.

## 6. Data & persistence

Plain JSON under `/data`: `rooms.json` (full room state) and append-only `events.jsonl` (cap ~500 events/room). The **worker process** flushes dirty rooms every ~2s and on shutdown, prunes presence idle >5 min, and keeps metrics fresh — the API never blocks realtime on disk. Refresh or full server restart must restore the board exactly.

## 7. UX / API surface expectations

REST: `POST /api/rooms`, `POST /api/rooms/:code/join` (returns memberId, role, color), `GET /api/rooms/:code` (snapshot), `GET /api/metrics`, `GET /api/health`. WebSocket messages (typed): `join`, `presence.update`, `job.create/update/move`, `stage.create/rename`, `event` (server→client), `resync`, `error`. Malformed messages get an error reply, never a crash. Layout targets laptop + tablet: top bar with room name, copyable code, connection pill (Live / Reconnecting / Offline), avatars, Activity button; formula bar; tabs along the bottom like a real workbook.

## 8. Quality, security, reliability

Validate every join and mutation server-side (name lengths, stage exists, version match). Rate-limit moves/edits (~10/s per member) and debounce presence broadcasts. No passwords for MVP — name-based entry with hard-to-guess room codes is acceptable. If the socket drops, the board becomes read-only with a clear banner.

## 9. Documentation & testing

README: the problem, `npm install` + `npm run dev` (starts web, API, and worker), how to open two browsers, test/smoke commands, data-file location, and an ASCII diagram of the realtime flow. Unit tests (Vitest): move/conflict reducer, stale-version rejection, role permissions, job-number generator, metrics counters. Smoke test (`npm run smoke`): boots API+worker on a test port, creates a room via REST, connects two WebSocket clients, moves a job, asserts both receive the same ordered event, restarts the API, asserts state restored from JSON and `/api/metrics` responds.

## 10. Constraints & non-goals

TypeScript everywhere (Node API + worker, Vite web); light npm deps only; fully local. No accounts, no OT/CRDT, no attachments, no real `.xlsx` import/export (CSV export is an optional stretch), no mobile app, no dashboards.

## 11. Acceptance criteria

- [ ] `npm run dev` boots web + API + worker; README steps are accurate
- [ ] Two sessions join the same room by code; both appear as colored avatars
- [ ] Create/edit/move of a job appears in the second session < 1s, no reload
- [ ] Simultaneous move of one job ends with identical state on both screens + one toast
- [ ] Refresh and full API restart both restore the board from `/data`
- [ ] Viewer role is blocked from mutating (UI and server)
- [ ] Presence highlight shows another user’s color/name on their selected row; idle after 60s
- [ ] Disconnect shows banner, auto-reconnects, replays missed events
- [ ] `/api/metrics` returns the counters above; logs are one JSON object per line
- [ ] `npm test` and `npm run smoke` both pass

## 12. Uniqueness / anti-clone constraints

Must speak print shop (job ticket, prepress, rush, pickup), use auto job numbers and sheet-tab stages — not Trello-looking generic kanban. No “Room 1 / User A” placeholders; ship a seeded demo room *Sunrise Signs & Print* with realistic jobs. The workbook surface (tabs, lettered grid, formula bar) is mandatory. Do not pivot to whiteboard/chat — the artifact is the job-ticket grid.

When done, print `DONE task_2: Multiplayer kanban board live sync` and start the next task immediately.

---

## Task 03 — Pair programming shared editor
**workdir:** `task_collaborative_realtime_03`
**id:** `collaborative_realtime_03_pair-programming-shared-editor`
**seed (original):** Build a pair-programming web app with a shared code editor, cursors for each user, chat sidebar, and session links. Use WebSockets for sync.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "resume_mid_task", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "medium", "value": "medium", "language_runtime": "javascript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "education", "ui_surface": "mobile_web", "persistence": "postgres_optional", "testing_depth": "browser_smoke", "novelty_hook": "plugin/extension hook (one stub plugin)", "delivery": "monorepo_client_server", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints Build-first: implement from PRD; forbid WebSearch/WebFetch and repo-wide fishing; code > research **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PLATFORM PROMPT — TandemShift

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

**TandemShift** is a mobile-web pair-programming room where a **rotating "driver" holds the keyboard** while navigators follow live cursors, chat in a sidebar, and get auto-nudged when it is their turn to drive. One-sentence pitch: *"Mob-style pairing sessions with a rotation timer, one-writer editing, and shareable session links — no install, works on a phone."*

Unlike generic whiteboard/chat demos, the collaboration metaphor is a **timed driver/navigator rotation** (mob programming). The domain twist: editing is **role-gated** — only the current driver can modify the shared code document; everyone else sees live updates and cursor positions. The rotation clock can hand off the keyboard automatically or on host tap.

**Audience voice:** enterprise engineering-enablement buyers — onboarding coordinators running ramp-up dojos, interview-loop facilitators, and incident-review leads. They care about role enforcement, durable session artifacts, and a guest experience that works in a mobile browser without accounts.

## 2. Target Users & Jobs-to-Be-Done

- **Enablement lead (host):** create a session, paste starter code, set rotation interval, share a link, keep the round moving.
- **Driver (rotating participant):** type in the shared editor during their turn; see their remaining time.
- **Navigator:** watch edits and cursors live, chat, queue a suggestion for their turn.
- **Guest reviewer:** join via link in view-only mode from a phone browser.

## 3. Core Requirements / Entities

Materialize these entities (names may vary, substance must not):

- `Session` — id, title, slug, language tag (e.g. `javascript`, `python`), starter code, rotation interval seconds, created_at.
- `Participant` — session_id, display name, role (`host | navigator | guest`; `driver` is a *state*, not a stored role), join token.
- `PresenceSession` — live socket connection: participant, online/idle/offline, cursor position (line/col), last seen.
- `DocumentState` — current code text, version counter, last editor.
- `ChatMessage` — session, author, body, timestamp, optional `system` flag (rotation notices post here).
- `RotationEvent` — audit log: who drove, start/end, trigger (`timer | host_advance | host_assign`).
- `InviteLink` — token, mode (`participant | guest`), expiry, revoked flag.

## 4. Major Feature Areas

### Sessions & membership
- Create session with title, language tag, starter snippet, rotation interval (30s–15min).
- Join via share link; choose display name. Guest links are view-only.
- Soft cap: 12 concurrent participants per session; overflow gets a friendly "session full" screen.
- Host controls: advance rotation, assign driver, pause timer, end session.

### Realtime editing with one-writer lock
- Shared code editor (textarea-based is acceptable; a lightweight editor component is a bonus — do not pull in a heavy IDE).
- **Conflict policy: single-writer lock.** Only the current driver's edits are accepted by the server; all others receive broadcast state. Cursor positions are last-write-wins. Chat is append-only. No OT/CRDT.
- Optimistic local typing for the driver; server rebroadcasts authoritative document with a version counter; non-driver clients snap to authoritative state.

### Presence & cursors
- Colored cursor/caret markers per participant with name labels, visible to all.
- Roster list: online/idle/offline dots, current driver badge, next-in-queue indicator.
- Connection status pill: `connected / reconnecting / offline`.

### Rotation engine
- Server-authoritative countdown; on expiry, keyboard passes to next online participant, a system message posts to chat, and the new driver's client shows a "You're driving" banner.
- Edge handling: driver disconnects → auto-advance after short grace period; only one participant → timer pauses.

### Chat sidebar
- Per-session chat with system messages interleaved (joins, handoffs, timer pauses).
- Debounced "typing…" indicator is optional; unread badge when sidebar is collapsed on mobile.

### Plugin hook (novelty — one stub plugin)
- Server exposes a minimal **plugin hook**: a `plugins/` directory where a module registering `onRotationEnd(ctx)` / `onSessionEnd(ctx)` hooks is auto-loaded.
- Ship **one working stub plugin**: `session-recap` — listens to rotation events and, on session end, posts a chat system message summarizing driver turns and durations. Document the hook interface in the README so buyers can imagine custom plugins (lint hints, compliance logging).

## 5. Domain-Specific Workflows

**Happy path:** Host creates session "API Onboarding Dojo — Wk 2" with 3-minute rotation → shares participant link → three navigators join from phones/laptops → host starts round → driver A edits, cursors of B/C visible → timer expires → system chat message, driver B gets banner and keyboard → host ends session → recap plugin posts summary → host copies session link for records; refresh restores full state.

**Edge cases to handle:** join with duplicate name (suffix or reject), expired/revoked link, driver drops mid-edit (grace + handoff), non-driver attempts edit (rejected with toast), reconnect within 30s restores role and cursor color, session full.

## 6. Data & Persistence Expectations

- **Postgres optional:** if `DATABASE_URL` is present, use Postgres via a tiny migration/DDL script; otherwise fall back to an in-process store (documented clearly). Same repository interface behind both.
- Durable: sessions, document state, chat history, rotation events, invite links must survive server restart (in Postgres mode) and page refresh (always, within process lifetime).
- Document autosaved with version counter; server is authoritative.

## 7. UX / API Surface Expectations

- **Mobile-web first:** responsive layout where chat collapses to a drawer, editor is usable at 360px width, touch-friendly driver banner and roster. Laptop layout: editor left, roster + chat right.
- Empty states that teach: first session screen explains "share link → start round."
- REST (or WS-RPC) endpoints for: create session, join, fetch state snapshot; WebSocket channel for: presence, edits, cursors, chat, rotation ticks/events. Server authoritative for membership, rotation, persistence.
- Accessible primary actions: create session, share/copy link, advance driver, send chat.

## 8. Quality, Security & Reliability

- Validate joins (token, capacity, name length) and all mutations (driver-only edit enforcement server-side — never trust the client).
- Rate-limit/debounce cursor and edit events (e.g. cursor updates ≤ 10/sec/client).
- Graceful degradation: offline banner + queued chat notice when socket drops; auto-reconnect with backoff.
- Invite tokens unguessable; guest tokens cannot become participants.

## 9. Documentation & Testing

- **Monorepo:** `server/` (Node.js + `ws` or Socket.IO) and `client/` (framework-free or light vanilla JS mobile-web SPA is fine; keep dependencies minimal), root `package.json` with workspace scripts.
- README: local run steps (one command to boot both), env vars (`DATABASE_URL` optional), plugin hook guide, reconnect behavior note, architecture paragraph on realtime flow.
- **Browser smoke test** (`npm run smoke`): boots the server, serves the client page, connects **two WebSocket clients simulating two browsers** through the full journey — join same session, driver edit → other client receives, cursor broadcast, rotation handoff, chat round-trip, refresh-restore of document — and asserts each. Must run headless in under ~60s with no external services in fallback mode.

## 10. Constraints & Non-goals

- JavaScript end-to-end; no TypeScript build pipeline required, no multi-GB deps, no Docker requirement.
- Not an IDE: no autocomplete, no execution/runner, no file trees — one shared document per session.
- No accounts/passwords; display names + invite tokens only.
- No OT/CRDT; the one-writer lock is the conflict policy by design.
- Exactly one stub plugin; the hook is the deliverable, not a plugin marketplace.

## 11. Acceptance Criteria

- [ ] Two browser clients join the same session via link and see each other's presence + cursors.
- [ ] Only the current driver can edit; server rejects non-driver edits; all clients converge without reload.
- [ ] Rotation timer hands off the keyboard automatically and posts a system chat message; host can also advance manually.
- [ ] Refresh mid-session restores document, chat, roster, and current driver.
- [ ] Guest link is view-only and enforced server-side.
- [ ] `session-recap` stub plugin posts a summary on session end; hook interface documented.
- [ ] `npm run smoke` passes the two-client sync journey.
- [ ] README runs the stack locally with and without Postgres.

## 12. Uniqueness / Anti-Clone Constraints

- **Forbidden:** generic "Socket.IO chat room" or whiteboard-tutorial clones, placeholder "Room 1 / User A" demos, lorem-ipsum UI.
- Required domain-authentic vocabulary throughout the UI and code: *driver, navigator, rotation, handoff, dojo, session recap*.
- Demo seed fixture must create a realistically named session (e.g. "Payments Service — Incident Retro Pairing") with believable starter code and chat, not filler text.
- The rotation lock + mobile-first layout + plugin hook combination is the differentiator; do not drop any of the three to save time.

When done, print `DONE task_3: Pair programming shared editor` and start the next task immediately.

---

## Task 04 — Live auction room
**workdir:** `task_collaborative_realtime_04`
**id:** `collaborative_realtime_04_live-auction-room`
**seed (original):** Create a real-time auction room platform: users join rooms, place bids, see live bid feed and countdown timers, and get notified when outbid.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "csharp", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "ecommerce", "ui_surface": "static_html", "persistence": "memory_only", "testing_depth": "smoke_only", "novelty_hook": "multi-theme or multi-difficulty presets", "delivery": "library_plus_demo_app", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups Build-first: no WebSearch/WebFetch/docs tours/winget-search installs; ≤2 local Greps then Write — low tasks must ship in few files **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# GavelDash — Real-Time Flash Auction Rooms (Library + Demo App)

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


## 1. Product identity

**GavelDash** is a small C# (.NET) real-time auction engine shipped as a reusable core
library plus a runnable demo web app. Collector clubs and community fundraiser hosts use
it to run rapid-fire "flash lots": participants join a room with a display name, place
bids against a live countdown, watch a bid-ladder chart update in real time, and get an
instant "you've been outbid" nudge. The signature twist is **pacing presets** — three
curated auction tempos (Lightning / Classic / Marathon) that change duration, minimum
increment, and anti-snipe extension, so one engine supports very different event styles.

## 2. Target users & jobs-to-be-done

- **Solo host / auctioneer** (the demo persona): spin up a room, pick a preset, list a
  lot, run the gavel, see the hammer price and winner.
- **Bidders**: join via room code, bid in one click, know immediately when outbid,
  watch time pressure visually.
- Jobs: "run a 60-second lot without chaos", "never lose to silence — get warned when
  outbid", "see price momentum at a glance".

## 3. Core requirements / entities

- `Lot` — id, title, starting price, state (Waiting/Live/Closed), hammer price, winner.
- `AuctionRoom` — room code, preset, lot, created-by (auctioneer), participant list.
- `Participant` — session token, display name, role (Auctioneer/Bidder), presence state.
- `Bid` — bidder, amount, server timestamp, sequence number.
- `PacePreset` — name, duration, min increment, anti-snipe window + extension seconds.
- `AuctionEvent` — typed feed entries (BidPlaced, Outbid, TimerExtended, LotClosed,
  Joined/Left) for the activity rail.

## 4. Major feature areas

- **Rooms & membership**: create room (choose preset) → get a 5-char share code; join
  with code + display name. Auctioneer is the creator; everyone else is a Bidder. Cap:
  12 concurrent participants per room. Rejoin with the stored session token restores
  identity and presence.
- **Presence & awareness**: live participant list with online/offline dot; activity
  feed rail showing joins, bids, extensions, and closes.
- **Bidding (server-authoritative)**: server validates amount ≥ current + increment,
  lot must be Live, a bidder may not outbid themselves. Accept → broadcast `BidPlaced`;
  previous high bidder receives a targeted `Outbid` event (client shows a toast/banner).
- **Countdown & anti-snipe**: server clock owns expiry. Any bid inside the preset's
  anti-snipe window extends the timer by the preset's extension seconds and broadcasts
  `TimerExtended`. At expiry the server closes the lot, sets hammer price + winner, and
  broadcasts `LotClosed`.
- **Dashboard charts (required UI surface)**: step-line chart of bid amount vs.
  sequence (hand-rolled SVG is fine), top-3 bidder podium bars, and a circular countdown
  ring. All update from realtime events without reload.
- **Pacing presets (novelty axis)**: Lightning (60s, +1, 5s→+5s), Classic (5m, +5,
  15s→+15s), Marathon (30m, +10, 60s→+60s). Also ship two CSS theme presets
  ("Podium Dark" / "Gallery Light") toggleable in the room header.

## 5. Domain workflows

**Happy path**: host creates a Classic room with lot "1987 Fleer Jordan sticker, starts
at 20" → shares code → 3 bidders join → auctioneer starts the lot → bids ladder up;
each outbid user sees a banner → a bid at T-12s extends the clock → timer hits zero →
winner banner + final hammer price on the chart.

**Edge cases**: bid below increment → rejected with reason; bid after close → rejected;
bidder disconnects mid-lot → presence flips offline, bids stand; rejoin resumes;
auctioneer closes early (restricted action, auctioneer-only); empty lot with zero bids
closes as "No sale".

## 6. Data & persistence

**In-memory only** (`ConcurrentDictionary` stores in the core library). No database, no
files. State survives client refresh via session token but is expected to vanish on
server restart — state this clearly in the README.

## 7. UX / API surface

- **Stack**: ASP.NET Core minimal APIs + **SignalR** for realtime; static vanilla
  HTML/JS/CSS dashboard page (no SPA framework).
- **HTTP**: `POST /rooms` (preset), `POST /rooms/{code}/join`, `POST /rooms/{code}/start`,
  `POST /rooms/{code}/close`, `POST /rooms/{code}/bids`.
- **Hub `AuctionHub`**: broadcasts `BidPlaced`, `Outbid` (targeted), `TimerExtended`,
  `LotClosed`, `PresenceChanged`.
- Layout: header (room code, preset badge, theme toggle, connection status pill:
  connected/reconnecting), left = chart + countdown ring, right = bid feed + podium
  bars + participant list. Empty state teaches "Share this code to open bidding".
- One primary action per panel with a label; keyboard-focusable bid button.

## 8. Quality, security, reliability

- Validate display names, amounts, and room codes server-side; reject with readable reasons.
- Rate-limit: max 5 bid attempts/sec/participant; ignore excess.
- Client shows a reconnecting banner on SignalR drop and resyncs room state on reconnect.
- Optimistic bid button disable until server confirms (no fake bid rendering).

## 9. Documentation & testing

- README (solo-dev voice): `dotnet run` steps for the demo app, architecture note on the
  realtime flow (HTTP join → hub group per room → server clock loop), preset table.
- **Smoke tests only**: one tiny xunit project with ~4 asserts against the core engine —
  create room, valid bid accepted, low bid rejected, outbid event emitted to prior leader,
  expiry closes lot with correct winner.
- **Static pass**: `dotnet build` and `dotnet test` must both succeed cleanly.

## 10. Constraints & non-goals

- No payments, escrow, real money, accounts/passwords, image uploads, or persistence.
- No multi-lot catalogs (one lot per room), no OT/CRDT, no mobile app.
- Keep it thin: target ≤ ~12 source files across `GavelDash.Core` + `GavelDash.Demo`
  + smoke tests.

## 11. Acceptance criteria

- [ ] Two browser sessions join the same room by code; bids appear in both without reload.
- [ ] Countdown is server-driven; anti-snipe extension visibly fires.
- [ ] Outbid banner reaches only the displaced bidder.
- [ ] Auctioneer-only start/close is enforced; a bidder's attempt is rejected.
- [ ] Bid chart, podium bars, and countdown ring update live.
- [ ] Disconnect/reconnect restores presence; connection pill reflects state.
- [ ] All three presets selectable and honored (duration/increment/extension).
- [ ] `dotnet build` + `dotnet test` pass; README runs the demo locally.

## 12. Uniqueness / anti-clone constraints

- Not a chat or whiteboard tutorial: all language must be auction-authentic (lot, gavel,
  hammer price, increment, anti-snipe, paddle/bidder). No "Room 1 / User A" placeholders —
  seed the demo with realistic lot names like "Sealed 1999 Pokémon booster pack".
- The pacing-preset system and the charts-first dashboard are core, not decoration; a
  generic bid text box without presets/charts fails the run.
- Do not add a database or auth scaffold "just in case" — memory-only is a hard constraint.

When done, print `DONE task_4: Live auction room` and start the next task immediately.

---

## Task 05 — Classroom quiz live leaderboard
**workdir:** `task_collaborative_realtime_05`
**id:** `collaborative_realtime_05_classroom-quiz-live-leaderboard`
**seed (original):** Build a live classroom quiz app where a teacher pushes questions and students answer in real time with a running leaderboard.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "approval_gated", "repo_state": "partial_scaffold", "tool_profile": "mixed", "user_persona": "staff_eng", "complexity": "hard", "value": "hard", "language_runtime": "cpp", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "education", "ui_surface": "game_loop_window", "persistence": "sqlite", "testing_depth": "unit_plus_smoke", "novelty_hook": "chaos toggle: inject one recoverable failure path", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths Build-first still applies: no online research loops; deepen the product with Write/Edit, not Explore agents **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PLATFORM PROMPT — Chalkwire

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

When done, print `DONE task_5: Classroom quiz live leaderboard` and start the next task immediately.

---

## Task 06 — Collaborative markdown notes
**workdir:** `task_collaborative_realtime_06`
**id:** `collaborative_realtime_06_collaborative-markdown-notes`
**seed (original):** Create a collaborative markdown notes app with rooms, live caret presence, version history snapshots, and export to Markdown/HTML.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "single_shot", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "low", "language_runtime": "rust", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "productivity_collab", "ui_surface": "cli_tui", "persistence": "json_file", "testing_depth": "smoke_only", "novelty_hook": "domain twist: niche audience + unusual constraint", "delivery": "single_readme_run", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups Build-first: no WebSearch/WebFetch/docs tours/winget-search installs; ≤2 local Greps then Write — low tasks must ship in few files **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PROJECT REQUEST — NetLog73

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


## Target users & jobs-to-be-done
- **Net control (owner):** starts the room, takes snapshots, restores/clears the log.
- **Check-in logger (operator):** joins with room code + callsign, appends and edits log lines.
- **Listener (guest):** read-only, follows the net live with caret awareness.

## Core entities
`Room{code,name,created_at,doc:Vec<Line>,members,snapshots,events}` · `Line{id,text}` · `Member{callsign,role:Owner|Operator|Listener}` · `Presence{callsign,line,col,status:Idle|Typing}` · `Lock{line_id,holder}` (in-memory only) · `Snapshot{id,label,at,doc}` · `Event{kind,callsign,at,summary}` (ring buffer, last 50).

## Major feature areas
1. **Rooms & membership.** `serve` starts a relay on `127.0.0.1:7373`. `join --code NET-K7 --call KD7ABC [--role listener]` creates the room if the code is new (first joiner = Owner) or joins it. Cap: 8 concurrent operators; listeners don't count toward editing but do toward the cap. Duplicate callsigns rejected with a clear message.
2. **Realtime transport.** Localhost TCP relay; newline-delimited JSON messages (`Join, Welcome, CaretUp, LockReq, LockAck, LineSet, LineAdd, LineDel, Snapshot, Restore, Leave, State`). Server is the sole authority: it mutates room state, persists, and broadcasts. Clients render what they receive; on disconnect the TUI shows `reconnecting…`, retries ~10s, and rejoins with full-state resync. Server releases all locks held by a dropped callsign.
3. **Collaborative artifact: the net log.** Document = ordered markdown lines. **Conflict policy: exclusive per-line lock (PTT).** Keys: arrows move caret; `Enter`/`i` = key up (lock line, edit inline); `Enter` = commit + key down; `Esc` = cancel + release; `o` = append new line below (auto-locked); `dd` = delete locked line. Lines locked by others render with a `▶KD7ABC` tag and refuse edits with a status message. Caret metadata is last-write-wins.
4. **Presence & activity feed.** Caret moves broadcast debounced (~250ms); remote carets render as colored inverse markers with callsign labels. Side feed shows joins, leaves, key-ups, snapshots, restores.
5. **Snapshots & history.** `Ctrl+S` prompts for a label and stores a full doc snapshot server-side. `netlog73 snapshots --code X` lists them; `netlog73 restore --code X --id N --yes` replaces the doc (broadcasts an event). Snapshots survive server restart.
6. **Export.** `netlog73 export --code X` writes `data/exports/<CODE>.md` and `<CODE>.html`. Hand-rolled mini markdown→HTML renderer (headings, bold, italic, inline code, `-` lists, paragraphs); HTML gets a header block with room name, export time, and participating callsigns.

## Domain workflows
**Happy path:** start server → two terminals join `NET-K7` as `KD7ABC` (owner) and `W1XYZ` → W1XYZ keys up line 3, types `K2QRP checks in, traffic: none`, keys down → KD7ABC sees the line and W1XYZ's caret move in under a second → `Ctrl+S "mid-net checkpoint"` → export.
**Edge cases:** editing a line another operator holds → refusal message naming the holder; listener pressing `i` → refused; 9th join → waitlist message; server restart → locks cleared, doc + snapshots intact; restore requires `--yes`.

## Data & persistence
One JSON file per room at `data/rooms/<CODE>.json`, written atomically (temp + rename) on every mutation. Locks and live presence are **not** persisted. Events capped at 50. Include a schema example in the README.

## UX surface
TUI layout: header (room name, code, your callsign, connection status ●), main doc pane with carets/lock tags, right activity feed, footer key help. Empty room shows: "Frequency clear. Press `o` to open the log. 73." CLI subcommands: `serve | join | export | snapshots | restore`. Raw-mode TUI is required — not a line prompt.

## Quality & reliability
Validate callsigns (3–7 uppercase alnum, ≥1 digit) and reject empty room codes. No panics on malformed input or disconnects. Debounce caret spam. All state transitions flow through the server (no client-side file writes).

## Documentation & testing
`README.md` with <60-second quickstart (serve + two joins), key table, architecture note (transport, authority, lock policy), and a scripted Field Day demo scenario. Smoke tests only (fast `cargo test`): protocol message round-trip, markdown→HTML renderer cases, lock acquire/conflict/release, snapshot+restore on the room struct.

## Constraints & non-goals
No auth/encryption beyond room codes; localhost-only by default; no OT/CRDT; no web UI; no generic "Room 1 / User A" content anywhere — demo data must be a plausible net log.

## Acceptance criteria
- [ ] Two client processes see each other's edits and carets live
- [ ] A locked line refuses a second editor with a named-holder message
- [ ] Rejoin after server restart restores doc + snapshots
- [ ] Listener role cannot mutate the doc
- [ ] `export` produces valid `.md` and `.html`
- [ ] Snapshot create/list/restore works via CLI
- [ ] `cargo build` + `cargo test` pass; README quickstart runs as written
- [ ] UI copy uses callsign/net terminology throughout

When done, print `DONE task_6: Collaborative markdown notes` and start the next task immediately.

---

## Task 07 — Ops war-room incident chat
**workdir:** `task_collaborative_realtime_07`
**id:** `collaborative_realtime_07_ops-war-room-incident-chat`
**seed (original):** Build an incident war-room chat with channels per incident, @mentions, severity tags, and a timeline of status updates synced live.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "medium", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "html_canvas", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "must include a live demo mode with sample data", "delivery": "docker_compose_optional", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints Build-first: implement from PRD; forbid WebSearch/WebFetch and repo-wide fishing; code > research **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# Flareline — Incident War-Room with a Live Ops Timeline

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


## Target users & jobs
- **Incident Commander (IC):** opens an incident, sets SEV level, posts status updates, drives to resolution.
- **Responders:** join via invite code, coordinate in channels, get pinged via @mentions.
- **Observers (guests):** read-only stakeholders watching the live timeline.

## Core entities
`Responder(id, handle, display_name)` · `Incident(id, title, sev[1-4], status[investigating|identified|monitoring|resolved], version, created_by)` · `Channel(id, incident_id, name)` (auto-created: `#ops`, `#comms`) · `Membership(incident_id, responder_id, role[ic|responder|observer])` · `Message(id, channel_id, author_id, body, seq)` · `StatusEvent(id, incident_id, author_id, kind[status_change|sev_change|note], payload, seq)` · `Invite(code, incident_id, role, expires_at)` · `PresenceSession(incident_id, responder_id, channel_id, last_seen)`.

Per-incident monotonic `seq` on all events — this is the replay cursor.

## Feature areas
1. **Incidents & membership:** create incident (creator becomes IC); join via 8-char invite code; observer invites enforced read-only; cap 20 concurrent participants/incident; server rejects joins beyond cap with a clear error.
2. **Channels & chat:** per-incident channels, append-only messages, @handle mention parsing (server-side) with per-user mention highlighting and an unread-mention badge.
3. **Severity & status lifecycle:** IC-only actions to change SEV1–SEV4 and incident status; every change emits a `StatusEvent`. Conflict policy: **last-write-wins guarded by incident `version`** — stale-version writes get `409`.
4. **Live ops timeline (canvas):** a full-width canvas strip per incident rendering StatusEvents as color-coded ticks (SEV colors), with hover tooltip, auto-scroll to newest, and a "jump to live" button when scrolled back. This is the primary collaborative artifact — it must redraw within ~1s of any peer's status change, no page reload.
5. **Presence:** per-channel online/idle dots, "viewing #ops" labels, 10s heartbeat, 30s idle timeout.
6. **Realtime transport:** single WebSocket endpoint (`/ws?incident=<id>`), JSON envelopes `{type, seq, payload}`. Server-authoritative ordering. Client may render own messages optimistically but must reconcile by `seq`.
7. **Reconnect:** client stores last-seen `seq`; on reconnect sends `resume:{last_seq}`, server replays missed events then goes live. Exponential backoff (max 15s). Connection pill states: `connected / reconnecting / offline`.
8. **Demo mode (required):** `--demo` flag seeds two realistic incidents (e.g. *"payments-api: elevated 5xx after deploy 1f3a9c"*, SEV2) with scripted bot responders who post messages, mentions, and SEV/status changes on a timer so a fresh visitor sees the timeline animating live.

## Workflows
**Happy path:** IC creates incident → sets SEV2 → shares invite → responders join `#ops` → post updates, `@sara check the lb logs` → IC posts status `identified` → timeline ticks appear live for all → IC marks `resolved`, timeline shows green terminal tick.
**Edge cases:** observer attempts to post → 403 + inline notice; two IC-grade actors change severity concurrently → version conflict, loser re-fetches; WS drops mid-incident → resume replay, no duplicate timeline ticks; >20 concurrent joins → queued observer offer; empty incident → canvas empty-state text "Post your first status update".

## Persistence
SQLite (WAL mode), all entities above plus an append-only `events` table enabling replay. Refresh fully restores channels, messages, and timeline. Migration runs at boot. DB path via env var, default `./flareline.db`.

## UX / API surface
- REST: `POST /incidents`, `POST /incidents/:id/invites`, `POST /join/:code`, `GET /incidents/:id/state`, `POST /incidents/:id/status` (IC only, version-checked), `POST /channels/:id/messages`. WS: `/ws`.
- Layout: channel list left, chat center, canvas timeline pinned top, presence rail right. Responsive down to tablet widths.
- Rate-limit messages (5/s per user, token bucket) and debounce presence heartbeats; on WS outage, chat input stays usable with queued-send disabled and an explicit banner.

## Quality & security
Validate handles (3–20 chars, `[a-z0-9_]`), invite codes, SEV/status enums. Parameterized SQL only. HTML-escape all rendered message bodies. Secrets not required beyond a session cookie (random token on join; no passwords in MVP).

## Testing & docs
- Go unit tests (light, `go test ./...` < 10s): mention parser, role enforcement (observer 403), incident version/LWW conflict, seq-ordered replay on resume, invite expiry.
- README: local run (`go run ./cmd/flareline [--demo]`), optional `docker compose up`, architecture note covering WS fan-out, seq/replay, and the LWW policy.
- Smoke script (`scripts/smoke.sh`): boots server, hits health + create + join, exits non-zero on failure.

## Constraints & non-goals
No message edits/deletes, no DMs, no file uploads, no OT/CRDT, no OAuth, no mobile app, no multi-workspace tenancy. Do not gold-plate.

## Acceptance criteria
- [ ] Two browser sessions in one incident see messages, presence, and canvas timeline ticks live without reload
- [ ] Invite-code join works; observer role is blocked from posting and status changes
- [ ] @mention renders highlighted and increments badge for the mentioned user
- [ ] Refresh restores full state from SQLite; WS reconnect replays via `seq` with no duplicates
- [ ] Concurrent severity change with stale version returns 409
- [ ] `--demo` mode shows a live, self-animating incident within 10s of first load
- [ ] `go test ./...` green; README steps work from a clean checkout

## Anti-clone constraints
This is not a Slack/Discord clone and not a Socket.IO chat tutorial. Mandatory domain language throughout UI and code: *Incident Commander, SEV1–SEV4, status lifecycle (investigating → identified → monitoring → resolved), ops timeline, war-room*. The canvas timeline is a first-class, live-synced artifact — not a decorative widget. Sample data must read like a real incident (service names, deploy SHAs, plausible responder handles), never "Room 1 / User A".

When done, print `DONE task_7: Ops war-room incident chat` and start the next task immediately.

---

## Task 08 — Shared music listening room
**workdir:** `task_collaborative_realtime_08`
**id:** `collaborative_realtime_08_shared-music-listening-room`
**seed (original):** Create a synchronized listening room: queue tracks, play/pause sync across clients, chat, and host controls.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "resume_mid_task", "repo_state": "partial_scaffold", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "java", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "media_cms", "ui_surface": "react_spa", "persistence": "memory_only", "testing_depth": "unit_plus_smoke", "novelty_hook": "offline-first; no cloud accounts", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths Build-first still applies: no online research loops; deepen the product with Write/Edit, not Explore agents **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# Crossfade Club — Synchronized Listening Rooms

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

**Crossfade Club** is a drop-in listening room for people in the same place — a house party, a study hall, a van on tour Wi-Fi. One person starts a room; friends join with a short code and a nickname. **No accounts, no emails, nothing in the cloud.** Everyone hears the same track at the same second, and one person's pause button stops every laptop in the room.

One-line pitch: *a shared turntable for the room you're actually in.*

Domain twist: rooms are **offline-first and LAN-friendly**. The server ships a built-in "crate" of procedurally generated instrumental loops — no audio files, no streaming APIs, no internet needed after install. Audio is rendered in the browser from tiny tone recipes, so the whole product runs on localhost forever.

## 2. Target users & primary jobs

- **The Host** (party host, study-group lead): start a room in seconds, keep the vibe, rescue a bad queue.
- **The DJ** (trusted friend): build and reorder the queue while the host watches the room.
- **The Listener**: hang out, chat, suggest tracks, step away and rejoin without breaking anything.

Jobs-to-be-done: press play once and trust a dozen laptops stay in sync; survive someone closing their laptop mid-song; let latecomers land *mid-track*, not back at the top.

## 3. Core entities (in-memory only)

`Room` (code, name, createdAt) · `Listener` (server-issued session token + nickname) · `Role` (HOST / DJ / LISTENER) · `Track` (id, title, bpm, tone-recipe JSON, durationSeconds) · `QueueEntry` (position, addedBy, source: crate|suggestion) · `PlaybackMark` (trackId, positionSeconds, playing, serverTimestamp, version) · `ChatMessage` · `Suggestion` · per-room event log (last 50 transport/queue events).

## 4. Major feature areas

- **Rooms & joining.** Create room → server returns a human-friendly code (4 letters + 2 digits, unambiguous alphabet, e.g. `JAZZ-07`). Join = code + nickname, nothing else. Caps: 12 listeners per room, 25 rooms per server; full rooms return a polite error. Host leaves → auto-promote longest-tenured DJ, else oldest listener. Empty for 10 minutes → room closes.
- **Synchronized playback (the heart).** Server owns the clock. Every play/pause/seek/skip becomes a versioned `PlaybackMark`; clients compute position = mark.position + (now − mark.serverTimestamp) and correct drift: > ~350 ms triggers a quick-fade resync, below that nothing audible. Late joiners receive the current mark and start mid-track. **Conflict policy: server-authoritative last-write-wins by version number**; stale-version commands are rejected with a fresh snapshot.
- **The crate & queue.** ~8 named built-in procedural loops (e.g. "Neon Rain — 92 BPM", "Rooftop Cassette — 76 BPM"), rendered via Web Audio from JSON recipes. DJs/hosts add, reorder, remove. Listeners submit to a **Suggestions bin** that host/DJ approve or dismiss. Empty queue → friendly "the crate is empty" idle state, never an error.
- **Chat.** In-room chat, last 100 messages kept, nickname color dots, rate limit 5 messages / 10 s per listener with a friendly throttle notice. Chat must remain readable while offline (last-known view).
- **Presence.** Listener list with role badges and away state (tab hidden 60 s). Persistent connection pill: Connected / Reconnecting… / Offline.
- **Host controls.** Promote/demote DJ, lock queue (locked = listeners can't even suggest), clear queue with confirmation, end room for everyone.
- **Offline-first resilience.** Session token + last known mark version in localStorage. On socket drop: SPA keeps last-known room state, holds chat drafts, shows the offline banner, retries with exponential backoff, then resyncs via snapshot — no manual refresh. Zero external calls anywhere: no CDNs, no web fonts, no third-party anything.

## 5. Key workflows

**Happy path:** host creates room → shares `JAZZ-07` → four listeners join → DJ queues three loops → host presses play → all clients land within ~0.4 s of each other → pause reaches everyone in under a second → a latecomer joins at 1:12 and hears it from 1:12.

**Edge cases:** duplicate nickname → auto-suffix "-2" · host's laptop closes mid-song → promotion happens and playback never stops · host scrubs seek repeatedly → server debounces to 4 transport events/s · two DJs reorder simultaneously → version rejection, loser auto-refreshes · server restarts → rooms are gone (expected with memory-only) → clients see "the room ended" with a one-tap "start a new room".

## 6. Data & persistence

In-memory only (concurrent maps). No database, no files, no disk. State must survive a **page refresh** (snapshot endpoint + session token) but **not** a server restart — document this loudly in the README and in the UI's room footer.

## 7. UX / API surface

- React SPA (Vite), dark "listening bar" aesthetic, responsive for laptop + tablet: now-playing hero with live progress bar, queue rail, chat column. Empty states teach the first action ("Drop your first track from the crate").
- REST: `POST /api/rooms` · `POST /api/rooms/{code}/join` · `GET /api/rooms/{code}/snapshot`.
- WebSocket `/ws`, typed JSON events: `transport.command`, `playback.mark`, `queue.add/remove/reorder`, `suggestion.new/resolve`, `chat.post`, `presence.update`, `role.change`, `room.state`, `error`.
- Accessible primary controls: big play/pause with aria-label, keyboard-focusable queue rows.

## 8. Quality, security, reliability

- Validate codes and nicknames (2–20 chars, no control characters); unknown codes → 404 with friendly copy.
- **The server enforces every role rule** — the UI never merely hides buttons.
- Cap chat at 300 chars; debounce transport floods; sync tolerance target ≤ 500 ms drift between any two localhost clients after correction.
- Graceful messaging whenever realtime is down; nothing fails silently.

## 9. Documentation & testing

- README with **one command to run everything** (e.g. `./dev.sh` builds the SPA and boots the Java server serving it on :8080) plus a short architecture note on the clock-sync flow with an ASCII sequence diagram.
- Unit tests (JUnit): playback-mark math, queue ordering rules, the role-permission matrix, the chat rate limiter.
- One-command smoke test: boots the real server, creates a room, joins two WebSocket sessions, asserts the host's play command reaches both clients and a pause follows. Verification is **runtime pass** — the app must genuinely boot and serve.
- Seed: server always starts with the 8-track demo crate preloaded.

## 10. Constraints & non-goals

Java 17+ (keep dependencies light — plain JDK HTTP server or a tiny lib), React SPA, in-memory only. No databases, accounts, OAuth, cloud services, real audio files, or Spotify/YouTube integration. Not a music library, not cross-day playlists, not a social network (no profiles, no follows).

## 11. Acceptance criteria

- [ ] One command starts backend + SPA; first screen offers "Start a room" and "Join with a code"
- [ ] Two sessions in one room: host play/pause/seek reflected at the second client within ~1 s
- [ ] Late joiner starts mid-track within ~1 s of live position
- [ ] Refresh keeps you in the room with queue and last-100 chat intact
- [ ] Listener role cannot reorder or pause — server rejects, UI explains
- [ ] Host departure promotes a successor; queue lock blocks suggestions
- [ ] Socket drop shows offline banner; auto-reconnect resyncs without manual refresh
- [ ] Chat rate limit triggers with a friendly message, never a crash
- [ ] Unit + smoke tests pass; README documents restart-wipes-rooms behavior

## 12. Uniqueness / anti-clone rules

No "Socket.IO chat tutorial" shapes: no `Room1`/`UserA` placeholders, no dead grey boxes. All copy speaks listening-room (crate, deck, queue, mark). The crate ships real named procedural loops that actually make sound — nothing placeholder-only.

When done, print `DONE task_8: Shared music listening room` and start the next task immediately.

---

## Task 09 — Live CSV co-editing sheet
**workdir:** `task_collaborative_realtime_09`
**id:** `collaborative_realtime_09_live-csv-co-editing-sheet`
**seed (original):** Build a lightweight collaborative spreadsheet for CSV data with cell editing, live sync, and conflict highlighting (not Excel-plugin).
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "multi_turn_repair", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "low", "value": "medium", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "data_analytics", "modality": "text_code", "ui_surface": "desktop_window", "persistence": "localstorage", "testing_depth": "integration_light", "novelty_hook": "accessibility-first keyboard UX", "delivery": "cli_entry_plus_ui"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups Build-first: no WebSearch/WebFetch/docs tours/winget-search installs; ≤2 local Greps then Write — low tasks must ship in few files **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# ReconGrid — Local-First Collaborative CSV Reconciliation Grid

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
**ReconGrid** is a keyboard-first, multi-window collaborative spreadsheet for reconciling CSV extracts. Two analysts open the same session in separate desktop browser windows; every committed cell edit appears in the peer window in near real time, and simultaneous edits to the same cell are surfaced as **disputes** to resolve — never silently overwritten.

- **One-sentence pitch:** "Pair-reconcile vendor CSVs in the browser with live sync, cell-level dispute flagging, and an exportable audit trail — no SaaS, no server database, data never leaves the machine."
- **Buyer lens (enterprise):** zero external data egress, seat-free local demo, auditable conflict history, CSV round-trip fidelity.
- **Domain twist:** reconciliation workflow — conflicts are first-class *disputes* with keep-mine / take-theirs resolution and a session audit log a controller can export.
- **Stack (locked):** TypeScript (Vite, vanilla TS — no framework), desktop browser window, `localStorage` persistence, thin CLI entry. Target: runnable in <10 minutes of build work.

## 2. Target Users & Jobs-to-be-Done
- **Ops/finance analyst pair** reconciling a vendor invoice extract against a baseline.
  - "We edit the same grid from two windows and see each other's fixes live."
  - "If we both touched a cell, I want it flagged and resolvable without a mouse."
  - "I export the reconciled CSV and the dispute log for sign-off."

## 3. Core Requirements / Entities
Materialize these (names flexible, substance not):
- **Session** (join code, owner id, created-at) — the collaboration space.
- **Participant** (display name, role: `owner | editor | viewer`, color chip, last-seen).
- **GridDoc** (headers, rows; all values strings; current committed state).
- **CellCommit** (event: row, col, old, new, author, timestamp) — capped audit log (last 200).
- **Dispute** (cell ref, mine value, theirs value, authors, status open/resolved).
- **PresencePing** (participant id, focused cell, idle flag).

## 4. Major Feature Areas
- **Sessions & membership:** create session → get 4–6 char code; join by code. First joiner is owner; subsequent joiners pick editor or viewer. Soft cap 6 participants; overflow joins as viewer. Identity persists across refresh (stored participant id).
- **Presence:** participant roster with color chips; each peer's focused cell outlined in their color; idle marking via `visibilitychange`; status pill: `Live · N participants` / `Solo — open another window with code XXXX`.
- **Cell editing & live sync:** click or Enter/F2 edits; Tab commits+moves; Esc cancels. Transport = `BroadcastChannel` per session code with `storage`-event fallback; `localStorage` is the durable authority. Commits apply optimistically locally and broadcast.
- **Disputes (conflict policy — pick and implement exactly):** committed state is **last-write-wins**, BUT a Dispute is opened when (a) a remote commit lands on a cell with an uncommitted local edit, or (b) two commits to the same cell with different values arrive within 2s. Disputed cells get a striped highlight + badge; resolution (keep-mine / take-theirs) writes a new commit, closes the dispute, and logs it.
- **CSV import/export:** import via file picker or paste (header row required; ragged rows padded with warning). Owner-only; importing while peers edit requires confirmation and broadcasts a doc-reset event. Export produces a faithful round-trip (correct quoting/escaping of commas, quotes, newlines) plus optional `disputes.csv` audit export.
- **Accessibility-first keyboard UX (novelty core):** ARIA `grid` role with roving tabindex; arrow-key navigation; full action set reachable without a mouse; visible focus ring; `aria-live="polite"` announcer narrates remote edits ("Row 4, Amount changed by Priya to 19.40") and new disputes; `Alt+D` jumps to next open dispute; `Ctrl+Z` undoes your last commit; `Ctrl+E` exports. No hover-only or drag-only interactions.

## 5. Domain Workflows
**Happy path:** Owner runs CLI → seeded demo session opens (vendor-invoice fixture) → second window joins by code → both edit cells, see live updates + presence outlines → simultaneous edit on one cell → dispute badge → `Alt+D`, choose take-theirs via keyboard → export reconciled CSV.
**Edge cases:** refresh mid-edit restores doc + identity and discards uncommitted edit; viewer attempts edit → rejected with announcement; BroadcastChannel unavailable → storage-event fallback with "degraded sync" pill; localStorage quota error → non-blocking toast, in-memory state kept; import-during-collaboration resets peers' grids with notice.

## 6. Data & Persistence
`localStorage` only, namespaced: `recongrid:session:<code>:doc | :events | :participants | :me`. State survives refresh; disputes survive until resolved. No server DB, no IndexedDB, no cookies.

## 7. UX / API Surface
- **CLI (`recongrid`):** `recongrid serve [--port N] [--seed demo]` serves the built app and prints the session URL/code; `recongrid --help` documents commands.
- **UI (single desktop window):** session bar (code, role, status pill, roster), grid region, disputes panel (list + resolve buttons, keyboard navigable), announcer live region. Empty state teaches: "Import a CSV or load the demo extract."

## 8. Quality, Security, Reliability
Validate CSV parse + join codes; debounce presence pings (~300ms); cap audit log; escape all cell content on render (no HTML injection); graceful messaging when sync is degraded.

## 9. Documentation & Testing
- README: run steps (`npm i`, `npm run dev` / CLI), two-window demo script, architecture note explaining BroadcastChannel + localStorage authority + fallback.
- **Integration-light tests (required, vitest + jsdom):** CSV round-trip; dispute policy (cases a & b); role gate (viewer edit rejected); two simulated clients sharing a storage/bus shim converge on the same doc.
- **Browser smoke (required):** `npm run smoke` — Playwright (chromium only) opens two windows on one session, edits a cell in A, asserts visibility in B, triggers and resolves a dispute, reloads and asserts persistence.

## 10. Constraints & Non-Goals
Not an Excel/Sheets plugin, no formulas, no formatting engine, no charts, no server/WebSocket backend, no auth beyond session code + role pick, no mobile layout work, no multi-doc accounts.

## 11. Acceptance Criteria
- [ ] Two windows join one session by code; edits sync without reload
- [ ] Simultaneous same-cell edit opens a dispute; keyboard-only resolution works
- [ ] Refresh restores grid, disputes, and identity
- [ ] Viewer role blocked from editing (tested)
- [ ] CSV export round-trips the demo fixture byte-faithfully
- [ ] Every primary action operable by keyboard; remote changes announced via live region
- [ ] Integration tests + browser smoke pass; README demo script accurate

## 12. Uniqueness / Anti-Clone Rules
No generic "Sheet1 / A1 / User A" placeholders — ship the seeded **vendor-invoice reconciliation fixture** (vendor, invoice #, PO match status, amount, variance, notes). UI copy must use reconciliation language (dispute, baseline, variance, sign-off), not chat/whiteboard terms. No Socket.IO whiteboard/chat clones; the dispute-resolution workflow and keyboard-first ARIA grid are mandatory differentiators, not optional polish.

When done, print `DONE task_9: Live CSV co-editing sheet` and start the next task immediately.

---

## Task 10 — Remote design critique board
**workdir:** `task_collaborative_realtime_10`
**id:** `collaborative_realtime_10_remote-design-critique-board`
**seed (original):** Create a real-time design critique board: upload images, pin comments with coordinates, resolve threads, and show live viewers.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "visual_diff", "session_shape": "approval_gated", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "media_cms", "ui_surface": "static_html", "persistence": "csv_files", "testing_depth": "smoke_only", "novelty_hook": "deterministic --seed for reproducible runs", "delivery": "notebook_plus_script", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths Build-first still applies: no online research loops; deepen the product with Write/Edit, not Explore agents **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# RemoteDesignCritique — Remote design critique board

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


## 1. Product identity
Build **RemoteDesignCritique** for category `collaborative_realtime`. Seed intent (honor this product, do not genericize away):

> Create a real-time design critique board: upload images, pin comments with coordinates, resolve threads, and show live viewers.

Artifact type: `web_fullstack`. Novelty hook: deterministic --seed for reproducible runs. Delivery: `notebook_plus_script`.

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

When done, print `DONE task_10: Remote design critique board` and start the next task immediately.

---
