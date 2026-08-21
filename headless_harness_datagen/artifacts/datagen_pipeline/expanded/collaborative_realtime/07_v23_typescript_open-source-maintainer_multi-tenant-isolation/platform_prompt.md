# VARIANT v23_typescript_open-source-maintainer_multi-tenant-isolation - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `typescript`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `multi_tenant_isolation`
- **ui_surface**: `html_canvas`
- **persistence**: `csv_files`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `typescript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v23_typescript_open-source-maintainer_multi-tenant-isolation`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v23_typescript_open-source-maintainer_multi-tenant-isolation` when demoable.

---

## BASE PRD (honor unless mutated above)

# Flareline — Incident War-Room with a Live Ops Timeline

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `go`
- **ui_surface:** `html_canvas`
- **persistence:** `sqlite`
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
