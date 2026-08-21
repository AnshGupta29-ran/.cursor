# VARIANT v39_javascript_security-auditor_chaos-fault-injection - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `javascript`
- **user_persona**: `security_auditor`
- **novelty_hook**: `chaos_fault_injection`
- **ui_surface**: `html_canvas`
- **persistence**: `localstorage`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `javascript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v39_javascript_security-auditor_chaos-fault-injection`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v39_javascript_security-auditor_chaos-fault-injection` when demoable.

---

## BASE PRD (honor unless mutated above)

# PROJECT REQUEST — NetLog73

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
