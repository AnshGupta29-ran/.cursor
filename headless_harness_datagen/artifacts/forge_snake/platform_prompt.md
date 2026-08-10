# VIPER TRACE — A* Snake Observatory

## 1. Project Request / Product identity

Build **Viper Trace**, a Python + Pygame Snake game with two souls: a responsive manual arcade mode and an AI mode where an A* "Trace Engine" pilots the snake and renders its planned route live on the grid. The defining hook: the AI is *survival-aware*, not greedy — before committing to a route it simulates the meal and verifies it can still reach its own tail afterward, and falls back to a space-maximizing "survival wander" when no safe route exists. Players watch the algorithm think via a path overlay, an explored-cells tint, live speed control, and difficulty presets that reshape grid size and obstacle layouts. Code-drawn primitives only, but cohesive: a deliberate two-tone-plus-accent palette, not default debug blocks.

## 2. Target users & primary jobs-to-be-done

- **Casual player:** wants tight manual Snake — buffered input, score, pause, instant restart.
- **Curious learner / demo audience:** wants to watch A* route around obstacles, see the planned path, and understand why the snake sometimes detours or deliberately stalls.
- **Verifier/developer:** wants deterministic, seedable runs and headless logic tests proving the AI is a real algorithm, not random thrashing.

## 3. Core requirements / entities

- **Grid world:** configurable cells-wide × cells-high; border walls always solid; no wraparound.
- **Snake:** ordered cell list, head-first; grows by 1 per pellet; collision with wall, obstacle, or self ends the run.
- **Food:** one active pellet on a free cell, placed by seeded RNG; value scaled by difficulty.
- **Obstacles:** static wall patterns per difficulty, defined in config data — never hardcoded into the game loop.
- **Modes:** `manual` and `ai`, chosen from a start menu or CLI flag.

## 4. Major feature areas

- **Core loop:** fixed-timestep ticks; direction input is queued and 180° reversals rejected so key spam can't cause unfair self-collision; pause/resume; restart from game-over screen without relaunch.
- **Trace Engine (AI mode):**
  - A* search, 4-neighborhood, Manhattan heuristic, treating body/walls/obstacles as blocked.
  - **Survival gate:** simulate eating along the candidate path; commit only if the post-meal head can reach the tail cell (BFS reachability).
  - **Fallback:** when no safe route exists, pick the legal move maximizing flood-fill reachable area (tail-chase acceptable); it must never choose a suicide move while a survivable one exists.
  - **Visualization:** draw the committed A* path as a distinct overlay (line/dots head→food); a second toggleable tint shows the last search's closed-set cells.
- **Difficulty:** ≥3 presets (e.g., Hatchling / Viper / Apex) varying grid size, starting speed, obstacle layout, score multiplier — all config-driven.
- **Speed control:** live +/- adjustment within bounds, both modes, current value on HUD.
- **HUD:** score, length, mode, difficulty, speed, and AI status using domain language: `TRACE: SAFE ROUTE`, `TRACE: SURVIVAL WANDER`, `TRACE: NO PATH`.

## 5. Domain-specific workflows

- **Manual happy path:** launch → menu → Manual + difficulty → play → die → game-over shows score + session best → `R` restarts, `Esc` returns to menu.
- **AI happy path:** menu → AI + difficulty → snake routes to food with visible path → overlay shifts to fallback styling during trap risk → game over reports pellets, ticks survived, fallback count.
- **Edge cases:** food never spawns on occupied cells (capped attempts, then board-full win handling); food sealed by obstacles triggers fallback without crash; quitting mid-run persists settings cleanly; `--seed N` reproduces the identical food sequence per difficulty.

## 6. Data & persistence

- Local JSON (project `data/` or user config dir): best score per difficulty+mode, last speed, difficulty, overlay toggles.
- Difficulty presets and obstacle layouts live in a readable config module/JSON.
- No accounts, no network, no external assets.

## 7. UX expectations

- Start menu, HUD, pause overlay, game-over screen — all navigable by keyboard.
- Distinct visuals for head vs. body, food, obstacles, planned path, explored tint; overlays legible over the grid.
- Controls table in README plus an in-game help line; audio optional and, if present, mutable with persisted preference.

## 8. Quality & reliability

- Logic (grid, snake, A*, survival gate, fallback) isolated from rendering in pure-Python modules testable headlessly.
- Deterministic tie-breaking in A*; seeded food RNG.
- Replanning cadence documented and bounded for a ≤40×30 grid; smooth on modest hardware.

## 9. Documentation & testing

- README: setup (`pip install pygame`), run commands, controls, difficulty descriptions, `--seed` usage, and a short design note on the Trace Engine (A* + survival gate + fallback).
- Headless tests covering: A* shortest path on open grid and around obstacles; A* returns none when sealed; survival-gate simulation; fallback refuses suicide when an alternative exists; snake move/grow/collision rules; food-spawn occupancy.
- Fast smoke script: fixed-seed headless AI run asserting score > 0 within N ticks.

## 10. Constraints & non-goals

- Python 3.10+, pygame as the sole runtime dependency (pytest allowed for tests).
- No ML/torch — the AI is classical search by design. No multiplayer, no asset downloads.
- Not a single-file tutorial script: config-driven levels, persistence, and the full Trace Engine are mandatory.

## 11. Acceptance criteria

- [ ] Documented entry point launches to a menu; manual and AI modes both playable end-to-end.
- [ ] AI uses genuine A* (Manhattan, 4-neighborhood) with the committed path visibly rendered; explored-set overlay toggleable.
- [ ] Test proves fallback never picks a lethal move when a survivable one exists.
- [ ] ≥3 difficulty presets alter grid/obstacles/speed; live speed adjustment reflected on HUD.
- [ ] Best scores and settings persist across runs; `--seed` reproduces food sequences.
- [ ] Headless logic suite and smoke run pass.
- [ ] README gets a first-time player into a session in under two minutes.

## 12. Uniqueness / anti-clone constraints

- Forbidden: the generic single-file Snake with hardcoded 20×20 grid and a "random-move AI." The survival-gated A* with flood-fill fallback and live path visualization are the product's identity.
- HUD and docs must use Trace Engine terminology (`SAFE ROUTE`, `SURVIVAL WANDER`), not "computer playing."
- No dead menu buttons, placeholder screens, or unused config — every listed feature ships working.
- should have no syntax and compilation error and game should be working. 