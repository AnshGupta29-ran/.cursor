# Deepvault Survey — ASCII Salvage Roguelike

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `typescript`
- **ui_surface:** `html_canvas`
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

## 1. Project Request / Product Identity

**Deepvault Survey** is a small, offline-first, turn-based ASCII roguelike rendered on an HTML canvas. The player is a junior **Reclamation Surveyor** descending three floors of a flooded, pre-Collapse data vault to recover the **Vault Heart**. The vault is guarded by derelict custodial machines ("husks"), light is scarce, and every expedition is procedurally generated from a visible seed so runs can be replayed and shared.

This is a product request from a non-technical product manager: behaviors and outcomes below are contractual; internal implementation choices are yours, within the locked stack.

- **Stack (locked):** TypeScript + Vite, HTML `<canvas>` rendering with a monospace font. No game engine.
- **Persistence (locked):** **memory only.** No localStorage, IndexedDB, files, cookies, or network calls. The "save" feature is an in-memory *Stasis Save* (see below) that lives and dies with the browser tab.
- **Delivery:** one command dev server (`npm run dev` after `npm install`), fully offline.
- **Repo state:** a partial scaffold may exist. Inspect and extend it — do not wipe and restart. Keep a short `STATUS.md` describing what is done/pending so a fresh session can resume mid-task.

## 2. Target Users & Jobs-to-Be-Done

- **Coffee-break roguelike players:** "I want a 10-minute run with real tension and a clear win condition."
- **Seed sharers:** "I want to tell a friend 'try seed K7X2' and know they get the same vault."
- **Skeptical reviewers:** "I want proof the generator, line-of-sight, and combat are real algorithms, with tests."

## 3. Core Requirements / Entities

- **Surveyor (`@`)**: HP 10, bump-to-attack melee (2 dmg), moves one tile per turn (8-way optional, 4-way minimum).
- **Tiles**: wall `#`, floor `.`, descent shaft `>`, unexplored = blank/dark.
- **Enemies (three distinct, documented behaviors — no random thrashing):**
  - **Rust Husk `h`** (HP 4, 1 dmg): wanders until player enters its 5-tile awareness radius, then chases via BFS pathfinding.
  - **Sentry Coil `s`** (HP 3, 2 dmg): immobile; if player shares a row/column with clear line of sight, it telegraphs one turn (glyph flashes), then zaps.
  - **Scav Rat `r`** (HP 2, 1 dmg): wanders; consumes any item it steps onto; attacks only when adjacent.
- **Inventory — exactly 3 item types, 3 slots, no stacking:**
  - **Patch Kit `+`** — restore 6 HP (cannot exceed max).
  - **Lumen Flare `o`** — vision radius expands 6 → 12 for 6 turns.
  - **Spark Charge `*`** — 4 damage to all enemies within radius 2.
- **Objective**: reach the shaft on floors 1–2; on floor 3, claim the **Vault Heart `&`** → victory screen. HP 0 → "Signal Lost" defeat screen.

## 4. Major Feature Areas

- **Procedural generation (seeded):** seeded PRNG (e.g., mulberry32); non-overlapping rooms connected by L-shaped corridors; every floor guaranteed fully connected (BFS-verifiable); shaft placed in the room farthest from spawn; enemy/item counts and enemy HP scale up per floor. Same seed ⇒ byte-identical floor layouts and spawn tables.
- **Fog of war:** three states per tile — unseen, remembered (dim), visible. Field of view via recursive shadowcasting (or equivalent symmetric algorithm), radius 6, blocked by walls.
- **Turn engine:** player acts → enemies act → status effects tick. Deterministic given a seed and input sequence.
- **Stasis Save:** a menu action captures a full in-memory snapshot (dungeon, entities, inventory, turn count, seed). Main menu offers **Resume from Stasis** restoring that exact state. One slot. README must state plainly that stasis is per-tab and lost on refresh — this is intentional, not a bug.
- **Scoring:** salvage = 25 × enemies defeated + 15 × items collected + 100 × depth reached − turns taken (floor of 0). Shown on the end screens along with the run seed.
- **Session flow:** main menu (New Expedition with optional typed seed, Resume, How to Play) → run → pause overlay (Esc/P) → victory/defeat screen with restart.

## 5. Domain Workflows

**Happy path:** open page → menu → New Expedition → explore floor 1, fog reveals as you move → pick up a Patch Kit (slot 1) → bump-attack a Scav Rat → flare reveals a Sentry's corridor → take the shaft `>` → floors 2–3 → claim Vault Heart → victory screen shows salvage score and seed.

**Edge cases to handle:** picking up with full inventory (leave item, show message); Spark Charge with no enemies in range (allowed but wasted, logged); Lumen Flare while already flared (refresh duration, not stack); Sentry zap interrupted by killing it during its windup (zap cancelled); Resume pressed with no stasis (disabled/greyed); using Stasis Save after death (refused — run is over); typed seed blank (auto-generate and display it).

## 6. Data & Persistence Expectations

Memory only, enforced. All state (run, stasis snapshot, settings such as they are) lives in module-scope objects. Zero network requests after initial page load; no external CDNs or fonts. State must be cleanly serializable to a plain object so the stasis round-trip can be unit-tested (serialize → restore → deep-equal).

## 7. UX Surface Expectations

- Canvas renders a cohesive glyph scene — colored ASCII on dark background, not debug rectangles; visible tiles lit, remembered tiles dimmed, unseen black.
- HUD: HP, depth (e.g., "D2/3"), seed, flare timer when active, three inventory slots with key hints (1/2/3), and a 3-line message log ("Rust Husk falls apart.", "Sentry Coil is charging!").
- Controls overlay in menu and README: WASD/arrows (+ optional hjkl/yubn), 1–3 use item, Esc pause, Enter confirm.
- Readable at default window sizes on modest hardware; stable frame, no flicker between turns.

## 8. Quality, Security & Reliability

- Deterministic rules documented in README (turn order, FOV radius, damage numbers).
- No `eval`, no remote assets, no telemetry. Dependency count kept minimal (Vite + test runner only).
- Game logic (generation, FOV, combat, inventory, stasis) must be pure/importable modules decoupled from canvas rendering so they run headless in tests.

## 9. Documentation & Testing

- **README:** premise, controls, win/lose conditions, run instructions, design notes (generation algorithm, FOV choice, each enemy behavior), module map, known limitations.
- **STATUS.md:** completed vs. pending items for mid-task resume.
- **Unit tests (Vitest or equivalent):** seed determinism (same seed → same layout), floor connectivity (BFS reaches every room), FOV blocked by walls and symmetric, combat math, inventory capacity/full-slot rule, stasis serialize→restore round-trip.
- **Smoke test (`npm run smoke`):** boots the dev server, fetches the page successfully, and runs a headless fixed-seed simulation of ≥100 turns with scripted inputs asserting no exceptions and valid state transitions; non-zero exit on failure.

## 10. Constraints & Non-Goals

- No multiplayer, no accounts, no cloud, no audio requirement.
- No persistent high scores across reloads (memory-only constraint wins over the usual template).
- No sprites/tilesets — ASCII glyphs only, styled cohesively.
- Not a NetHack clone: no orcs/goblins/dragons, no "dungeon level" terminology — vault fiction throughout.

## 11. Acceptance Criteria

- [ ] `npm install && npm run dev` launches a playable session offline.
- [ ] Menu → seeded new run → three floors → victory, and a separate defeat path, both with restart.
- [ ] Fog of war shows unseen/remembered/visible distinctly; flare alters FOV as specified.
- [ ] All three enemy behaviors observably distinct; Sentry telegraphs before zapping.
- [ ] Inventory enforces 3 slots; all three items work as specified.
- [ ] Stasis Save + Resume restores an identical state mid-run; refused after death.
- [ ] Same typed seed reproduces the same floors across two runs.
- [ ] Unit tests pass (`npm test`) and smoke test passes (`npm run smoke`).
- [ ] README lets a first-time player start, play, and understand scoring in <2 minutes.

## 12. Uniqueness / Anti-Clone Constraints for This Run

This is **not** a generic fantasy dungeon crawler: keep the drowned-vault salvage fiction, machine-husk enemies, surveyor terminology ("expedition", "shaft", "stasis", "salvage"), and the seeded-expedition identity. Forbidden: placeholder-only screens, a text-only "game", unlabeled copied tutorial code, or renaming this into a generic "Rogue clone". Every enemy and item above must exist with the specified behavior — do not silently cut scope; if time presses, reduce floor count scaling polish, never features.
