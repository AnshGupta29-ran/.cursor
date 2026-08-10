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
