# VARIANT v40_typescript_student-hacker_audit-trail-export - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `typescript`
- **user_persona**: `student_hacker`
- **novelty_hook**: `audit_trail_export`
- **ui_surface**: `dashboard_charts`
- **persistence**: `memory_only`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `typescript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v40_typescript_student-hacker_audit-trail-export`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v40_typescript_student-hacker_audit-trail-export` when demoable.

---

## BASE PRD (honor unless mutated above)

# SheetFlow — Live Job-Board Workbooks for Print & Sign Shops

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `typescript`
- **ui_surface:** `excel_workbook`
- **persistence:** `json_file`
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
