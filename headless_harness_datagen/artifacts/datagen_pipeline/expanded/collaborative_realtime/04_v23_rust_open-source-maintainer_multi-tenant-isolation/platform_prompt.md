# VARIANT v23_rust_open-source-maintainer_multi-tenant-isolation - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `rust`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `multi_tenant_isolation`
- **ui_surface**: `html_canvas`
- **persistence**: `csv_files`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `rust`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v23_rust_open-source-maintainer_multi-tenant-isolation`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v23_rust_open-source-maintainer_multi-tenant-isolation` when demoable.

---

## BASE PRD (honor unless mutated above)

# GavelDash — Real-Time Flash Auction Rooms (Library + Demo App)

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `csharp`
- **ui_surface:** `static_html`
- **persistence:** `memory_only`
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
