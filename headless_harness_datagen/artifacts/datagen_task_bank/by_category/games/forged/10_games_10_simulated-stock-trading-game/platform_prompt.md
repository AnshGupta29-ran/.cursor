# PROJECT OBJECTIVE — SeedStreet Exchange

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `go`
- **ui_surface:** `static_html`
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

## 1. Product identity
**SeedStreet Exchange** is a deterministic, seed-locked paper-trading arena set on the fictional **Meridian Archipelago commodities market**. The fantasy: you are a solo floor trader working one compressed "market day" (240 ticks) across procedurally named island instruments (KELP, BRINE, AMBR, SALTGLASS…). The signature twist: **the entire market is a pure function of a seed** — same seed, same prices, same news shocks, forever. Luck is eliminated; the leaderboard is a fair fight. Tagline: *"Same seed, same storm."*

## 2. Target users & jobs-to-be-done
A solo dev/demo player who wants a 5-minute skill-based trading run. Jobs: (1) start a run on a chosen seed, (2) read a chart and place buy/sell orders as the clock advances in steps, (3) survive to the settlement bell and see profit ranked on a per-seed leaderboard, (4) inspect any leaderboard entry's full trade tape.

## 3. Core requirements / entities
- **Instrument**: symbol, display name, sector, base price, drift, volatility — 5 instruments derived deterministically from the run seed.
- **Tick**: integer clock 0–239 (one market day). No wall-clock anywhere in game state.
- **Price function**: `price(seed, symbol, tick)` — pure, stateless, computable on demand. Log-space regime-switching random walk driven by an internal PRNG you control (implement splitmix64/xorshift; do **not** rely on `math/rand` global behavior). 2–3 **Dispatch events** (news shocks) per day land at seed-derived ticks and jolt one sector.
- **Run**: id, seed, trader handle, starting cash 10,000 credits, status active/settled.
- **Trade**: run_id, tick, symbol, side, qty (whole shares, long-only, no margin), price, fee.
- **Ledger/leaderboard**: settled runs ranked by profit, filterable by seed; each row links to its trade tape.
- **Rules**: fee 0.15% per side (min 1 credit); insufficient cash or shares rejected; advancing past tick 239 force-liquidates at final prices and settles.

## 4. Major feature areas
- **Trading floor page** (server-rendered): portfolio summary (cash, holdings, mark-to-market equity), per-symbol inline **SVG price chart** (full history up to current tick), order form (symbol, side, qty), "Advance 1 / 10 / 30 ticks / to close" controls.
- **Dispatch banner** rendered at event ticks with flavor text ("Storm over the kelp flats — KELP sector shock").
- **Settlement page**: final equity, profit, return %, equity curve SVG, trade tape, leaderboard rank.
- **Leaderboard page**: global + per-seed filter; deterministic ordering (profit desc, then settled-tick asc, then run id asc); expandable tape view.
- **Snapshot mode** for visual-diff verification: `--snapshot` flag serves a fully populated canned run frozen at a fixed tick; page output must be byte-identical across repeated fetches and restarts (no timestamps, no random ordering, tick-based labels only).

## 5. Domain workflows
**Happy path:** home → enter handle + seed (default from `--seed`) → run created → buy KELP 40 @ tick 0 → advance 10 → dispatch banner appears → sell half → advance to close → settlement page → leaderboard shows run; tape page lists all trades with tick/price/fee.
**Edge cases:** overspend rejected with inline error, portfolio unchanged; oversell rejected; trade on settled run rejected; advancing past 239 auto-settles exactly once (idempotent settle); two runs on the same seed taking identical actions must yield identical profits (determinism guarantee); restart mid-run resumes from SQLite at the correct tick.

## 6. Data & persistence
SQLite file (`seedstreet.db`, path via `--db`). Tables: `runs`, `trades`; leaderboard as a query/view over settled runs. Suggested driver: pure-Go `modernc.org/sqlite` (no cgo). Everything else Go standard library. No migrations framework — schema created idempotently at startup.

## 7. UX / API surface
Static server-rendered HTML via `html/template` + HTML form POSTs; **no SPA, no websockets**; minimal or zero JS. Routes: `GET /` (menu + leaderboard), `POST /run/new`, `GET /run/{id}` (floor, `?snapshot=1` stable variant), `POST /run/{id}/trade`, `POST /run/{id}/advance`, `POST /run/{id}/settle`, `GET /run/{id}/tape`, `GET /leaderboard?seed=`. CLI: `seedstreet --seed <int> [--port 8080] [--db seedstreet.db] [--snapshot]`.

## 8. Quality, security, reliability
Determinism is the core quality bar: price function pure and PRNG version-stable; identical seeds reproduce identical series across processes and restarts. Server-side validation on all order inputs; HTML escaped; integer tick arithmetic (prices stored as integer cents to avoid float drift). Single-process scope; graceful handling of bad run ids (404).

## 9. Documentation & testing
- `README.md`: run instructions, rules (fees, long-only, settlement), price-model + PRNG notes, seed semantics, route map.
- `NOTEBOOK.md`: narrated, reproducible walkthrough — numbered steps with exact `curl`/browser actions and expected page fragments for one full seed-7 run.
- `scripts/smoke.sh`: builds, boots server with `--seed 7`, asserts home/floor pages contain expected strings, executes a full buy→advance→sell→settle flow via curl, asserts leaderboard row exists, and runs the same flow twice asserting **identical profit** (determinism check). Non-zero exit on failure. Smoke-level testing only — no large suites.

## 10. Constraints & non-goals
Not real market data and no real-money language (credits only). No auth/accounts — handles are per-run labels. No multiplayer, no realtime ticking; step-advance is the intended loop. No heavy assets — typographic layout + inline SVG only. No external services.

## 11. Acceptance criteria
- [ ] `go build ./...` succeeds; server boots with `--seed`/`--port`/`--db`.
- [ ] New run on seed S shows 5 instruments; identical S reproduces identical prices after restart.
- [ ] Buy debits qty×price+fee; overspend/oversell rejected inline; state unchanged.
- [ ] Dispatch events fire at identical ticks for identical seeds.
- [ ] Advance past tick 239 force-liquidates; settle is idempotent.
- [ ] Leaderboard persists across restart; per-seed filter works; tape page complete with fees.
- [ ] Snapshot mode returns byte-identical HTML on repeated fetches (visual-diff ready).
- [ ] `scripts/smoke.sh` passes end-to-end including the determinism assertion.
- [ ] README + NOTEBOOK.md enable a first play session without prior context.

## 12. Uniqueness / anti-clone constraints
This is **not** a generic number-go-up clicker or a real-ticker clone. Required: fictional archipelago terminology (ticks, dispatches, settlement bell, trading floor), procedurally named instruments, seed-deterministic market as the central mechanic, fee-bearing trades, and tape-inspectable leaderboard. No AAPL/TSLA, no placeholder charts, no lorem-ipsum UI, no "TODO" stubs.
