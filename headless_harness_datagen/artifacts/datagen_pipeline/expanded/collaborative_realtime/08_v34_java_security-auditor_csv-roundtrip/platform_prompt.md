# VARIANT v34_java_security-auditor_csv-roundtrip - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `java`
- **user_persona**: `security_auditor`
- **novelty_hook**: `csv_roundtrip`
- **ui_surface**: `react_spa`
- **persistence**: `localstorage`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `java`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v34_java_security-auditor_csv-roundtrip`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v34_java_security-auditor_csv-roundtrip` when demoable.

---

## BASE PRD (honor unless mutated above)

# Crossfade Club — Synchronized Listening Rooms

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `java`
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
