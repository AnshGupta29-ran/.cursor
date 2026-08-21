# Rustwake: Core Rush — Turn-Based Tactics Skirmish

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `typescript`
- **ui_surface:** `html_canvas`
- **persistence:** `localstorage`
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

## 1. Project Request / Product Identity

**Rustwake: Core Rush** is a small browser game: a turn-based tactics skirmish on a square grid. Two rival salvage crews fight in a junkyard over a crashed hauler's power core. The player commands the **Copperjacks**; the computer runs the **Ferroscouts**. A match lasts 5–10 minutes and ends when one crew is wiped out **or** someone carries the core to their extraction edge — two live win paths, not just "kill everything."

Build it in **TypeScript (Vite)** with an **HTML5 Canvas** board, **localStorage** persistence, enemy AI computed in a **Web Worker**, and a tiny **Node/TypeScript API** whose only job is observability (structured logs in, metrics out). No accounts, no downloads, no game engine.

## 2. Target Users & Jobs-to-be-Done

Casual tactics fans who want a quick think-y match against the computer.
- *"I want to start a skirmish in under 10 seconds, no signup."*
- *"I want to close the tab mid-match and resume later."*
- *"I want to see *why* a shot hit or missed (odds shown before I commit)."*
- *"As the PM, I want a live count of matches played and wins/losses so I know the demo is being used."*

## 3. Core Requirements / Entities

- **Board**: 12×9 grid. Tile types: `open`, `crate` (half cover: blocks movement, softens shots), `container` (full cover: blocks movement and line of sight), `core spawn`, plus each crew's `extraction row` (their home edge).
- **Units** — 3 per side, fixed classes with distinct stats (HP / move range / attack range / damage):
  - **Bruiser**: 10 HP, move 3, melee (range 1), dmg 4.
  - **Runner**: 6 HP, move 5, range 2, dmg 2 — the natural core-carrier.
  - **Spotter**: 5 HP, move 3, range 5, dmg 3 — ignores the target's half-cover penalty.
- **The Core**: a pickup on the center tile. Adjacent unit spends 1 action to grab it; a carrier that is defeated drops it on a neighboring open tile.
- **Turn model**: sides alternate; each unit has **2 action points** per turn. Move (up to its range, BFS path around obstacles) costs 1; attack costs 1 and ends that unit's turn. "End turn" always available.
- **Combat**: base hit chance 80%; 55% if the target has a crate between it and the attacker (adjacent-cover rule, documented simply); containers block the shot entirely. Damage is fixed per class. Odds preview shown before confirming. Randomness uses a **seeded PRNG**; the seed is stored with the match for reproducibility.
- **Win / lose**: wipe the enemy crew **or** extract the core to your home row. Turn cap of 40; on cap, winner = more units alive, tiebreak = total HP, else draw.

## 4. Major Feature Areas

- **Match flow**: main menu → New Skirmish (pick 1 of 3 maps + difficulty) → play → result screen (winner, turns, cause) → Play Again / Menu.
- **Config-driven maps**: 3 hand-authored junkyard layouts in a JSON data file — not hardcoded in logic.
- **Enemy AI ("Scrapbrain")**: a real utility-scoring algorithm, not random moves. For each unit it scores candidate actions (damage reachable, distance to core/carrier, ends turn next to cover, retreat if HP ≤ 2) and picks the best, tie-broken by the seeded RNG. AI runs inside a **Web Worker** so the canvas never stutters; on worker failure, fall back to main-thread scoring and log a warning. Difficulty = AI gets a deliberate 15% "pick second-best action" blunder rate on Easy.
- **Observability**: the game emits structured JSON log events (`match_start`, `turn_start`, `move`, `attack`, `hit`, `miss`, `unit_down`, `core_pickup`, `match_end`) with session id, match id, turn number, and timestamp. Events buffer locally and batch-POST to the API.
- **Persistence**: save/resume mid-match, settings, and match history in localStorage (keys/versioned schema below).
- **HUD & polish**: HP bars, action-point pips, movement-range highlight, attack preview with hit %, current-turn banner, game-over screen. Drawn with canvas primitives + glyphs/labels — no art assets, but no bare debug rectangles either.

## 5. Domain Workflows

**Happy path**: open app → menu → New Skirmish → hover a unit (range highlights) → move → preview shot shows "55% — target behind crate" → confirm → End Turn → worker computes Ferroscouts' turn → animations/log panel update → someone wins → result saved to history → metrics counter increments.

**Edge cases** (must behave sanely):
- Reload mid-match → "Resume Match" restores board, turn, AP, core position, RNG seed.
- Carrier defeated → core drops on nearest open adjacent tile.
- Unit boxed in with no moves → may still attack or pass.
- Turn 40 reached → tiebreak rules produce a definite result.
- API offline → logs keep buffering (cap 200 events), game never blocks on telemetry; buffer flushes when the API returns.

## 6. Data & Persistence

localStorage, all values JSON with a `v` schema version:
- `rustwake.save` — full serializable match state (map id, units, core, turn, rng seed/state, difficulty).
- `rustwake.settings` — difficulty, AI speed, reduced-flash toggle, telemetry opt-out.
- `rustwake.history` — last 10 results (map, winner, turns, cause, date).
- `rustwake.logbuffer` — capped FIFO of unsent events.

Server side: the API appends received events to `logs/events.jsonl` and keeps in-memory counters (no database).

## 7. UX / API Surface

- Canvas ~960×720, mouse-driven (click select, click tile to move, click enemy to preview/confirm attack), keyboard: `Esc` deselect, `Enter` end turn, `P` pause overlay. A first-run controls overlay + README explain everything in plain words.
- A small on-screen log strip ("Spotter hit Bruiser for 3 — Bruiser down") so combat is legible without dev tools.
- API (Node stdlib `http`, TypeScript, documented port, CORS open to localhost):
  - `GET /health` → `{ "ok": true }`
  - `GET /metrics` → JSON: uptime, `matches_started`, `matches_completed`, `wins_player`, `wins_ai`, `turns_played`, `attacks`, `hits`, `avg_turns_per_match`, `log_events_received`.
  - `POST /logs` → accepts `{ events: [...] }` batches, body size-capped, validates shape, 400s on junk.

## 8. Quality, Security & Reliability

- Deterministic, seeded combat; seed visible in the result screen for bug reports.
- AI worker call has a 2s timeout with documented fallback.
- No personal data in logs; telemetry opt-out honored immediately.
- All pure rules (combat, cover, line of sight, pathfinding, win checks) live in dependency-free modules importable by tests and the worker alike.

## 9. Documentation & Testing

- **README.md**: what the game is, how to run (`dev`, `api`, `smoke`, `test`), controls, full combat/cover rules in plain language.
- **DESIGN.md**: turn model, Scrapbrain scoring summary, log event schema, known limitations.
- **Unit tests (Vitest)**: cover/hit-chance math, BFS movement range, line-of-sight blocking, win/tiebreak rules, seeded-RNG reproducibility, and one AI sanity test (AI prefers attacking a reachable carrier over a distant healthy unit).
- **Smoke test (`npm run smoke`)**: boots the API, asserts `/health` and `/metrics` shape, then plays a scripted headless match through the logic modules to a definite result within 40 turns. Non-zero exit on any failure. Everything must pass at delivery.

## 10. Constraints & Non-Goals

- TypeScript only; light deps (Vite, Vitest; Node stdlib for the API). No engines, no asset downloads, no network play, no accounts, no sound files required.
- Desktop-browser first; mobile layout is out of scope.
- Not a roguelike campaign, no tech trees — one great skirmish loop.

## 11. Acceptance Criteria

- [ ] `npm install && npm run dev` opens a playable match from the menu in under 10 seconds.
- [ ] All three unit classes exist with the stated stats and visibly different behavior.
- [ ] Crate and container cover affect hit odds exactly as documented; odds preview matches resolution.
- [ ] Both win paths (elimination and core extraction) and the turn-40 tiebreak work.
- [ ] Mid-match reload → Resume restores the exact state including RNG position.
- [ ] AI completes its turn via the Web Worker, uses the utility scoring described, and Easy difficulty is measurably sloppier than Normal.
- [ ] Structured events are emitted for every event type listed and appear in `logs/events.jsonl` via `POST /logs`.
- [ ] `GET /metrics` returns all listed counters and they change after a played match.
- [ ] With the API stopped, the game still plays fully and buffers logs without errors.
- [ ] `npm run test` and `npm run smoke` both pass.
- [ ] README lets a first-time player understand controls and rules unaided.

## 12. Uniqueness / Anti-Clone Constraints

- This is **not** chess, checkers, or a reskinned "grid tactics tutorial": the salvage fantasy (crew classes, power core, extraction rows, junkyard cover) must appear in all names, UI copy, and logs.
- Dual win condition (elimination **or** extraction) is mandatory — a pure deathmatch is a rejection.
- AI must be the documented utility scorer; random-move opponents are a rejection.
- No placeholder-only UI: tiles, units, cover, and the core must be visually distinguishable with labels/glyphs, and the hit-odds preview must exist.
