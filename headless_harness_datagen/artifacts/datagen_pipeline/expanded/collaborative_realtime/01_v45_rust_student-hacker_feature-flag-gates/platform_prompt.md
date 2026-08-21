# VARIANT v45_rust_student-hacker_feature-flag-gates - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `rust`
- **user_persona**: `student_hacker`
- **novelty_hook**: `feature_flag_gates`
- **ui_surface**: `desktop_window`
- **persistence**: `memory_only`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `rust`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v45_rust_student-hacker_feature-flag-gates`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v45_rust_student-hacker_feature-flag-gates` when demoable.

---

## BASE PRD (honor unless mutated above)

# BridgeLine — Incident-Bridge Team Chat (API-only, Python + SQLite)

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `api_only`
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
