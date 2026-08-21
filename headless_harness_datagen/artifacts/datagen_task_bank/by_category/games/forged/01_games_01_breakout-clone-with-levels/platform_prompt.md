# Core Tap — Abyssal Survey Rig

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `html_canvas`
- **persistence:** `json_file`
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

## 1. Project Request / Product identity
Build **Core Tap**, a single-player Breakout/Arkanoid-style arcade game in Python 3.10+ with Pygame. The player pilots a deep-sea **survey rig** (paddle) reflecting a **sonar pulse** (ball) to fracture **rock strata** (bricks) and extract ore across a chain of drill sites (levels). Written for a staff-engineer reader: deterministic rules, stated invariants, no magic numbers. Not a generic reskin — domain terminology, themed brick classes, and a run **snapshot export/import** system are first-class features.

## 2. Target users & primary jobs-to-be-done
- **Solo arcade player:** jump into a 3–8 minute run, chase a local leaderboard.
- **Tinkerer:** author/edit levels and export/import run snapshots as plain JSON.
- **Reviewer/CI:** verify the game headlessly via unit tests and a static preview build — no display required.

## 3. Core requirements / entities
- **Rig (paddle):** player-controlled; impact position sets rebound angle; clamped speed.
- **Pulse (ball):** fixed launch speed, slight speed-up per brick cleared, hard speed cap; sub-stepped collision so no brick is ever tunneled through.
- **Strata (bricks):** `sediment` (1 hit, 50 pts), `ore` (1 hit, 150 pts, high module drop rate), `core` (3 hits, visibly cracks, 300 pts), `basalt` (indestructible blocker).
- **Modules (power-ups, ≥4):** `wide_rig`, `split_pulse` (multiball, max 3), `drag_field` (slows pulses 6s), `pierce_charge` (pass-through 5s), `spare_hull` (+1 life). Timed effects stack by **refresh**, never duration-add.
- **Hull integrity (lives):** 3 per run; a pulse lost below the floor costs 1.
- **Sites (levels):** ≥3 shipped layouts, loaded from JSON files.

## 4. Major feature areas
- **Game loop:** menu → playing → paused → site-clear → game-over/win; fixed-timestep update.
- **Scoring:** per-class points × site depth multiplier.
- **Drop system:** seeded RNG (`ore` 35%, others 10%); seed recorded in snapshots for reproducibility.
- **Pause:** P or Esc; freezes physics and module timers; overlay lists controls.
- **High scores:** top-10 local leaderboard; 3-char callsign entry on game over/win.
- **Snapshots:** F5 export / F9 import mid-run; full state — site index, score, hulls, brick bitmap, pulse positions/velocities, active module timers, RNG state, schema version.
- **Static preview build:** `python -m coretap.preview` runs an autopilot rig under SDL dummy video and writes `preview/*.png` plus a `preview/index.html` contact sheet.

## 5. Domain-specific workflows
**Happy path:** launch → menu → start run → clear sites 1–3 → survey-complete screen → enter callsign → score persisted.
**Edge cases:**
- Snapshot during pause or mid-multiball → import restores exactly (deep-equal).
- Corrupt/tampered/unknown-version snapshot → clear error message; current run untouched.
- Missing/corrupt `highscores.json` → regenerate empty, never crash.
- Malformed level JSON → validation error naming file and field; that site refuses to start.
- Pulse at max speed → swept collision invariant holds (no skipped bricks).
- Window close mid-run → settings and leaderboard flushed to disk.

## 6. Data & persistence (JSON files only)
- `levels/site_01..03.json`: ASCII glyph grids (`s`/`o`/`c`/`b`/`.`), drop tables, speed ramp.
- `saves/highscores.json`, `saves/settings.json` (difficulty, mute, game speed), `saves/snapshot_<slot>.json`.
- All writes atomic (tmp + rename); all reads schema-validated with a `version` field.

## 7. UX surface expectations
- 60 FPS window (~900×600); cohesive abyssal palette; distinct glyph/color per brick class — no bare debug rectangles.
- HUD: score, hulls, site name/depth, active module icons with seconds remaining.
- Controls on menu and pause overlays: ←/→ or A/D move, Space launch, P pause, F5/F9 snapshot.
- Win/game-over screens with restart (R) and menu (Esc). Audio: optional generated beeps; must run silently if mixer is unavailable.

## 8. Quality, security, and reliability
- Pure-logic modules separated from rendering (`core/` vs `render/`): physics, scoring, drops, snapshot codec, level loader.
- Determinism: seeded RNG per run; documented invariants (speed cap, refresh-stacking, reflection angles).
- Graceful degradation: no display → preview and tests still pass; no audio device → silent mode.

## 9. Documentation & testing
- `README.md` (staff-eng voice): setup (`pip install -r requirements.txt && python -m coretap`), controls, win conditions, **snapshot format spec**, design notes with invariants and tradeoffs, known limitations.
- Light unit tests (pytest or unittest): scoring/multiplier, reflection math, module timer refresh, level JSON validation, **snapshot export→import round-trip deep-equality**, and a headless smoke test (init + 120 ticks, no exceptions). One command: `python -m pytest -q`.

## 10. Constraints & non-goals
- Python 3.10+, Pygame, stdlib, and pytest only. No asset downloads; drawn primitives only.
- No multiplayer, no network calls, no level-editor GUI, no global leaderboard.
- Lean medium-complexity MVP: polish the listed loop instead of adding features.

## 11. Acceptance criteria
- [ ] Window launches into a playable session; menu/pause/game-over/win flows all work
- [ ] ≥3 JSON-defined sites with distinct layouts; depth multiplier applies
- [ ] ≥4 module types including multiball; timers refresh-stack and expire correctly
- [ ] 3 hulls; pulse loss → respawn or game over; top-10 leaderboard persists to JSON
- [ ] F5/F9 snapshot export/import; corrupted import rejected safely
- [ ] Unit test proves export → import → deep-equal game state
- [ ] Headless run generates `preview/` static build (PNGs + `index.html`)
- [ ] `python -m pytest -q` green; README enables first play in under 5 minutes

## 12. Uniqueness / anti-clone constraints for this run
- Forbidden: "BREAKOUT" title screens, generic red/blue brick rows with no classes, placeholder/TODO UI, tutorial-verbatim structure.
- Required: abyssal survey terminology across UI, saves, and schema; glyph-driven level files; snapshot round-trip shipped as a player-facing feature (not only a test); staff-engineer design notes.
