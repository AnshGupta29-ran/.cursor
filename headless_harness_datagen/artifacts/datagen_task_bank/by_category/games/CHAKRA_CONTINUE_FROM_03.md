# CONTINUE games marathon from Task 03 (Tasks 01-02 already done)

Model note: continue on **gpt-oss-120b**. Do NOT redo tasks 01-02.

Already done:
- task_games_01 — Breakout (DONE)
- task_games_02 — Rustwake tactics (built under task_games_02/; verify smoke if needed, then mark DONE task_2)

Rules: complete tasks 03→10 in order; separate workdirs; no approval pauses; print DONE task_N then continue.

---

## Task 03 — Endless runner
**workdir:** `task_games_03`
**id:** `games_03_endless-runner`
**seed (original):** Create an endless runner with procedural obstacles, score distance, difficulty ramp, and restart flow (canvas or Pygame).
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "resume_mid_task", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "medium", "value": "medium", "language_runtime": "javascript", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "gaming", "ui_surface": "react_spa", "persistence": "sqlite", "testing_depth": "browser_smoke", "novelty_hook": "plugin/extension hook (one stub plugin)", "delivery": "monorepo_client_server", "modality": "text_code"}
**Time budget (medium):** finish within ~15 minutes / prefer ≤18 tool-heavy turns; solid MVP — core features + light tests, avoid gold-plating. Stop at a demoable MVP — do not keep polishing past the budget.

### Platform prompt (implement this)

# RegRun — Compliance Courier Ops

## 1. Project Request / Product Identity

Build **RegRun**, an endless-runner micro-game an enterprise L&D or compliance lead can drop onto an intranet to make security-awareness training measurable and repeatable. The player is a **Compliance Courier** sprinting across a procedurally generated **risk landscape**, vaulting **Audit Findings**, ducking under **Policy Gaps**, and grabbing **Control Badges** for score multipliers. Distance survived = "coverage meters"; difficulty escalates through named **Risk Tiers**. One twist: a **Daily Audit Seed** — everyone in the org runs the identical course each day, feeding a department leaderboard. One extension point: a **plugin hook** for custom obstacle/training packs, shipped with one working stub plugin.

Stack is locked: **JavaScript everywhere, React SPA client (canvas-rendered game), Node/Express server, SQLite persistence**, delivered as a **monorepo (`/client`, `/server`, `/plugins`)**.

## 2. Target Users & Jobs-to-be-Done

- **Compliance program owner (buyer):** deploy on-prem with zero external calls, view participation via run history, extend content without a vendor engagement.
- **Employee (player):** play a 60–120 second session, compete on today's seed, restart instantly after a wipeout.
- **Developer/integrator:** add a training-pack plugin against a documented contract.

## 3. Core Requirements / Entities

- **Run**: id, callsign, seed, mode (`daily`|`practice`), distance_m, risk_tier_reached, badges, duration_ms, created_at.
- **Player**: callsign only (typed at menu; no auth, no passwords).
- **Obstacle classes**: `AuditFinding` (ground block → jump), `PolicyGap` (overhead bar → slide), `DeadlineGate` (paired block+bar). AABB collision, documented.
- **Pickup**: `ControlBadge` — +1 combo multiplier (max ×5); a hit resets combo, not the run.
- **RiskTier**: `tier = floor(distance / 250)`; scroll speed, spawn density, and pattern table scale per tier via a documented formula.
- **Plugin descriptor**: name, version, obstacle types contributed, spawn rules.

## 4. Major Feature Areas

- **Core loop (canvas in a React component):** auto-run, Space/↑ jump, ↓ slide, P/Esc pause. Deterministic seeded RNG (mulberry32); same seed + same inputs → same course. Target 60fps with simple vector shapes (cohesive palette, not debug rectangles).
- **Procedural generation:** pattern-based spawner (gap table per tier), guarantees survivable spacing; pure functions in `client/src/game/` separable from rendering.
- **Difficulty ramp:** tier-ups announced in HUD; speed/density formulas documented in README.
- **Daily Audit Seed:** server derives today's seed (UTC date hash); client fetches it for `daily` mode; `practice` uses a random seed.
- **Restart flow:** game-over panel with run summary (meters, tier, badges, personal best), **R** to restart same mode, **M** for menu.
- **Persistence & leaderboard:** server saves each finished run; top-10 leaderboard filterable by seed; settings (mute, difficulty assist, reduced motion) saved per callsign.
- **Plugin hook:** server scans `/plugins/*/plugin.json` + `index.js` exporting `register(api)` where `api` exposes `addObstacleType(def)` and `addSpawnRule(fn)`. Ship stub plugin **phishing-surge** adding a `PhishNet` overhead obstacle at tier ≥ 2. Expose loaded plugins at `GET /api/plugins`; document authoring in README.

## 5. Workflows

**Happy path:** open app → enter callsign → menu → "Daily Audit" → run → collide → game-over summary auto-posted → press R → new run → leaderboard shows placement.

**Edge cases:** server unreachable → client plays offline, stores run in localStorage flagged `unsynced`, leaderboard panel shows "offline"; duplicate callsign allowed (leaderboard keys on run id); tab blur auto-pauses; invalid plugin manifest is skipped with a server log line, never a crash; SQLite file created/migrated on first boot.

## 6. Data & Persistence

SQLite (better-sqlite3 or sqlite3) at `server/data/regrun.db`. Tables: `runs`, `settings(callsign PK, json)`. No ORM required; migrations = idempotent `CREATE TABLE IF NOT EXISTS`. All data local — no telemetry, no external network calls (procurement requirement).

## 7. UX / API Surface

React SPA: Menu, Game (canvas + HUD: meters, tier, combo, speed), Game Over, Leaderboard, Settings. Controls overlay on first run; colorblind-safe palette; assist mode (slower base speed) toggle.

API: `GET /api/health` · `GET /api/seed/today` · `POST /api/runs` · `GET /api/leaderboard?seed=&limit=` · `GET /api/plugins` · `GET/PUT /api/settings/:callsign`. JSON, validated bodies, 4xx on bad input.

## 8. Quality, Security, Reliability

Deterministic rules documented; seeded RNG unit-testable; server validates run payloads (plausibility bounds, reject NaN/negative); no eval of plugin code beyond `require` of local files; parameterized SQL only; graceful shutdown closes DB.

## 9. Documentation & Testing

README: run commands (`npm install`, `npm run dev` for client+server, `npm start` for prod), controls, win/lose rules, difficulty formulas, plugin authoring guide, known limitations. `npm run smoke`: boots server + built client, drives a headless browser (Playwright or equivalent) asserting menu renders, canvas paints non-blank pixels, and a posted run appears in the leaderboard; if no headless browser is available, fall back to HTTP-level assertions and document the fallback. Plus one small unit-test file covering RNG determinism and the tier/spawn math.

## 10. Constraints & Non-Goals

No auth, no multiplayer, no assets beyond code-drawn shapes, no build step heavier than Vite, no external CDNs/fonts, no multi-GB deps. Not a full training platform — no user management or reporting dashboards.

## 11. Acceptance Criteria

- [ ] `npm run dev` serves playable game; jump/slide/pause/restart (R) all work
- [ ] Seeded generation is deterministic; daily mode uses server seed
- [ ] Difficulty visibly ramps across tiers; game-over posts run to SQLite
- [ ] Leaderboard and settings persist across server restarts
- [ ] Stub plugin loads, appears in `/api/plugins`, and its obstacle spawns at tier ≥ 2
- [ ] Offline mode degrades gracefully; `npm run smoke` passes
- [ ] README enables first play in under 2 minutes

## 12. Uniqueness / Anti-Clone Rules

Not a generic Dino clone: compliance-courier fantasy, named obstacle classes, Risk Tier system, Daily Audit Seed leaderboard, and the plugin contract are mandatory vocabulary and mechanics. No placeholder UI, no "TODO" screens, no tutorial-app copy. All copy uses domain-authentic training terminology.

When done, print `DONE task_3: Endless runner` and start the next task immediately.

---

## Task 04 — Minesweeper with solver hint
**workdir:** `task_games_04`
**id:** `games_04_minesweeper-with-solver-hint`
**seed (original):** Build Minesweeper with difficulty presets and a hint mode that highlights a safe deduction when possible.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "csharp", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "gaming", "ui_surface": "desktop_window", "persistence": "memory_only", "testing_depth": "smoke_only", "novelty_hook": "multi-theme or multi-difficulty presets", "delivery": "library_plus_demo_app", "modality": "text_code"}
**Time budget (low):** finish within ~8 minutes / prefer ≤12 tool-heavy turns; thin MVP — few files, minimal polish, ship a runnable demo. Stop at a demoable MVP — do not keep polishing past the budget.

### Platform prompt (implement this)

# Fathom Fields — Deduction-First Harbor Sweeping (PRD)

## 1. Project Request / Product identity
**Fathom Fields** is a desktop-window, single-player deduction game in **C# (.NET)**: a harbor has been seeded with anchored hazards, and the player charts safe water by sweeping soundings (cells) and marking hazards. Mechanically it is minesweeper-grade, but the identity is its own: nautical terminology, named difficulty presets, runtime color themes, and a signature **Hint Buoy** system that doesn't just point — it *explains the deduction* ("All 2 hazards around (4,2) are marked → (4,3) is safe"). Docs are written in a first-person solo-dev voice.

**Delivery shape:** one logic **class library** (`FathomFields.Core`) + one **desktop demo app** (`FathomFields.Desktop`) + one zero-dependency **smoke harness** (`FathomFields.Smoke`). Thin MVP: few files, runnable, no polish spiral.

## 2. Target users & primary jobs-to-be-done
- Casual logic players: launch, pick a preset, finish a board in 1–10 minutes, restart instantly.
- Learners of deduction: press **H** and learn *why* a cell is safe, not just that it is.
- The solo dev (portfolio): show a clean logic/UI split with deterministic, testable rules.

## 3. Core requirements / entities
- `Cell`: state `Hidden | Swept | Marked`, `AdjacentHazards` count, `HasHazard`.
- `Chart` (board): width, height, hazard count, **generation seed**; pure logic, no UI references.
- `GameSession`: state `Ready | Running | Won | Lost`, elapsed time, marks placed, hints used.
- `DifficultyPreset` (exactly three, named): **Rowboat** 9×9/10, **Trawler** 16×16/40, **Freighter** 30×16/99.
- `ThemePreset` (exactly three, named): **Daylight Harbor**, **Night Watch**, **Signal Flags** — full board/HUD palettes switchable mid-session.
- `Hint`: kind (`SafeWater | CertainHazard | NoForcedMove`), target cell(s), human-readable reason string.

## 4. Major feature areas
- **Chart generation:** hazards placed *after* the first sweep; first clicked cell **and its neighbors** are guaranteed hazard-free. Seeded RNG — same seed ⇒ identical chart.
- **Play mechanics:** left-click sweep, right-click mark, chord (sweep neighbors of a satisfied number — only when adjacent mark count equals the number; wrong marks block silently, never auto-trigger). Flood-reveal on zero-count cells. Marks beyond the preset's hazard count are rejected. Sweeps on marked cells are ignored.
- **Hint Buoy engine (rule-based, no guessing):** evaluate frontier constraints in order —
  1. satisfied number ⇒ all its remaining hidden neighbors are `SafeWater`;
  2. number − adjacent marks == hidden-neighbor count ⇒ all those neighbors are `CertainHazard`;
  3. subset rule: if constraint A's hidden set ⊂ B's and counts are equal, B ∖ A is safe.
  Return the first found deduction with a reason string; if none exists, return `NoForcedMove` and say so honestly in the UI. Highlight the target cell distinctly (e.g., buoy-gold outline) and append the reason to a visible **deduction log** panel. Hints increment a counter shown on the HUD.
- **HUD:** hazards remaining, elapsed seconds, active preset, session state; win/lose banner with restart; on loss, reveal all hazards (misplaced marks shown crossed-out).
- **Controls overlay:** toolbar buttons + keys: `H` hint, `R` restart, `1/2/3` presets, `T` cycle theme.

## 5. Domain-specific workflows
- **Happy path:** launch → Freighter/Daylight defaults → first sweep is safe → play with marks/chords → `Won` banner shows time and hints used → `R` starts a fresh chart.
- **Edge cases:** first-click safety on any seed; chord on unsatisfied or wrongly-marked number = no-op; hint on a board with no forced move = clear message, no information leaked; preset switch mid-run abandons the current chart with a fresh seeded one; Freighter sized so the window fits the grid at a fixed cell size (no scrolling hacks).

## 6. Data & persistence
**Memory only.** Theme choice, active preset, and per-preset best times live in a session-scoped in-memory store and vanish on exit. No files, registry, databases, or appdata — this is a hard constraint.

## 7. UX / API surface expectations
- Suggested stack: **WinForms on `net8.0-windows`** (add `EnableWindowsTargeting=true` if the build host is not Windows). One owner-drawn grid surface (`Panel` + `Paint`), not hundreds of buttons.
- Library API (UI-agnostic): `NewChart(preset, seed)`, `Sweep(x,y)`, `ToggleMark(x,y)`, `Chord(x,y)`, `RequestHint()`, `State`, events or return DTOs for cell changes — the desktop app must contain **zero game rules**.
- Controls table in README; the window title must read "Fathom Fields", never "Minesweeper".

## 8. Quality, security, reliability
- Deterministic rules; all randomness flows through the injected seed.
- Guard invalid input (out-of-range coords, actions after Won/Lost) without crashing.
- Full-board operations (reveal, hint scan) complete in a few ms on Freighter size. No network, no external assets, no NuGet beyond the platform SDK.

## 9. Documentation & testing expectations
- **README** (first-person solo dev): how to build/run (`dotnet build`, run Desktop, run Smoke), controls, the three hint rules explained, known limitations (e.g., no guess-free board guarantee beyond first click).
- **Smoke harness** (`FathomFields.Smoke`, plain console app, no test framework): asserts — seeded reproducibility; first-click safety across ≥20 seeds; flood-reveal invariant (revealed zero-region has no hazard neighbor); each hint rule fires correctly on crafted boards; win detection after sweeping all safe water. Prints PASS/FAIL lines, non-zero exit on failure.

## 10. Constraints & non-goals
- C#/.NET only; desktop window only; memory-only persistence. Do not add Unity, web views, or file saves.
- No auto-solver/play, no animations beyond the hint highlight, no sound, no multiplayer, no custom board-size editor (the three presets are the scope).

## 11. Acceptance criteria
- [ ] `dotnet build` succeeds; `FathomFields.Desktop` opens a playable window.
- [ ] Smoke harness passes all checks and exits 0.
- [ ] First sweep is always safe (cell + neighbors) on every seed.
- [ ] All three presets and three themes work; theme switch applies live without restart.
- [ ] Hint returns a rule-based deduction **with a reason string**, and honestly reports `NoForcedMove`.
- [ ] Win and loss flows both reach a banner and allow restart via `R`.
- [ ] Nothing is written to disk; best times reset between launches.

## 12. Uniqueness / anti-clone constraints
- Branding, harbor terminology (chart, sounding, hazard, mark, sweep, buoy), and preset/theme names above are **required** — reject any generic "Minesweeper clone" labeling in UI or README.
- The explanation-first hint log is the differentiating feature; a hint that silently reveals a cell is a defect.
- No placeholder UI, no dead toolbar buttons, no "TODO" screens — every visible control must function.

When done, print `DONE task_4: Minesweeper with solver hint` and start the next task immediately.

---

## Task 05 — Card battler prototype
**workdir:** `task_games_05`
**id:** `games_05_card-battler-prototype`
**seed (original):** Create a simple collectible card battler: deck, draw, mana, and a basic AI opponent turn.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "approval_gated", "repo_state": "partial_scaffold", "tool_profile": "mixed", "user_persona": "staff_eng", "complexity": "hard", "value": "hard", "language_runtime": "cpp", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "gaming", "ui_surface": "html_canvas", "persistence": "json_file", "testing_depth": "unit_plus_smoke", "novelty_hook": "chaos toggle: inject one recoverable failure path", "delivery": "one_command_dev_server", "modality": "text_code"}
**Time budget (hard):** finish within ~25 minutes / prefer ≤25 tool-heavy turns; full PRD depth — richer acceptance criteria and verification. Stop at a demoable MVP — do not keep polishing past the budget.

### Platform prompt (implement this)

# Brineglass Beacon — Collectible Card Battler (C++17 + HTML Canvas)

## 1. Project request / product identity
Build **Brineglass Beacon**, a single-player collectible card battler. Fantasy: two rival lighthouse keepers duel across a night reef, spending **Lumen** (mana) to summon sea **Allies** and cast **Signals** until one beacon's **Integrity** falls from 20 to 0. A **C++17 backend owns 100% of the rules** and serves a static **HTML Canvas** client; match state persists to **JSON files**. One command (`./run.sh`) builds and serves everything on `localhost:8080`.

Domain lexicon (use everywhere; no generic card-game copy): Lumen refills each turn with +1 max (cap 8); Allies arrive "swamped" (no attack that turn) unless **Surge**; **Shelled** = taunt; **Undertow** = escalating fatigue damage (1,2,3…) when drawing from an empty deck.

## 2. Target users & jobs-to-be-done
- A solo player wanting a 5–10 minute tactical duel in the browser, zero install.
- A staff-engineer maintainer who wants the rules engine separable from transport and verifiable headless — correctness must not require a browser.

## 3. Core entities
- **Card**: id, name, cost, kind (Ally|Signal), atk/hp, keyword (none|Shelled|Surge), rules text, flavor line.
- **Card pool**: ≥14 distinct cards in `data/cards.json`; content is data, not code.
- **Decks**: two preconstructed 30-card decks in `data/decks.json` — *Gullrigger* (low curve, aggressive) and *Reefwarden* (Shelled-heavy, controlling). Player picks one; the AI takes the other.
- **Player state**: integrity, max/current lumen, hand, board (≤5 Allies), deck, undertow counter.
- **Match**: turn number, active player, rng seed, action log, idempotency ledger.
- **Actions**: `play_card`, `attack`, `end_turn` — the only legal state mutations.

## 4. Major feature areas
- **Deterministic rules engine** (pure C++, no I/O): seeded RNG used only for the opening shuffle; same seed + same action sequence ⇒ identical match. Every applied action is appended to the log.
- **Turn structure**: Start (max lumen +1 to cap 8, refill, draw 1 / Undertow), Main (play, attack), End. Combat: attacker targets an enemy Ally or the enemy beacon; **Shelled Allies must be attacked first**; Ally-vs-Ally damage is simultaneous; dead Allies leave the board.
- **AI opponent "The Warden"** (a real algorithm, not random): greedy heuristic with lethal check — enumerate legal actions, score each (lethal-now = top priority; favorable trades; damage per lumen; avoid dumping the hand), apply the best, repeat until only `end_turn` remains. Difficulty: *Normal* runs full scoring; *Easy* skips lethal detection and holds back its costliest playable card. Document the scoring function in `DESIGN.md`. The Warden must never emit an illegal action.
- **Chaos toggle — "Lantern Flicker"** (setting or `?chaos=1`): the server fails ~15% of `POST /api/match/action` calls with `503` + error envelope **before** mutating anything. Every action carries a client-generated idempotency key; a repeated key replays the stored response instead of double-applying. Client auto-retries (≤3, small backoff) and shows a "Lantern flickering…" indicator. The match stays completable and the save uncorrupted.
- **Persistence**: after every applied action, atomically write `data/match.json` (temp file + rename). On match end, update `data/stats.json` (wins, losses, streak). `data/settings.json` holds difficulty + chaos. Boot with an unfinished match ⇒ menu offers **Resume**.
- **Canvas client**: everything game-visible is drawn on one `<canvas>` — both boards, hand, lumen gems, integrity dials, End Turn button, scrolling log strip, hover tooltips, select-then-target with a drawn arrow, win/lose overlay with Rematch. DOM only for the page shell and a controls hint.

## 5. Workflows
**Happy path:** `./run.sh` → open `localhost:8080` → menu (deck, difficulty, chaos) → alternate turns; Warden's plays appear in the log → integrity hits 0 → result screen → stats persist → rematch.
**Edge cases:** Undertow escalation on deck-out; full board (5) blocks summoning with a clear reason; illegal action ⇒ `409` + reason, state untouched; browser refresh mid-match ⇒ state reloaded; server restart mid-match ⇒ Resume works; chaos 503 bursts ⇒ retries recover with no duplicate plays; malformed bodies rejected cleanly.

## 6. Data & persistence
JSON files only: `cards.json`, `decks.json`, `match.json` (autosave, atomic, `"v":1` schema tag), `stats.json`, `settings.json`. The API redacts the AI's hand contents (count only) — no hidden-info leaks.

## 7. UX / API surface
`GET /` (shell+JS) · `POST /api/match/new` · `GET /api/match/state` (redacted) · `POST /api/match/action` (idempotency key required) · `POST /api/match/resume` · `GET|POST /api/settings` · `GET /api/stats`. Board readable at 1024×768; controls discoverable without opening the README.

## 8. Quality, security, reliability
- No runtime network calls; vendored single-header HTTP server and test framework are acceptable — builds need only a C++17 compiler (cmake or one g++ line).
- Server validates every action through the engine; never trust client-side lumen/integrity math.
- Engine invariants: lumen ≥ 0, board ≤ 5, each Ally attacks ≤1×/turn, Shelled targeting enforced, Undertow increments exactly once per empty draw.

## 9. Documentation & testing
- `README.md`: one-command run, controls, rules summary, repo map. `DESIGN.md`: turn loop, Warden scoring, Lantern Flicker recovery design, known limitations.
- **Unit tests** (engine only, no GUI): lumen curve, combat incl. Shelled and simultaneous death, Undertow, seeded-shuffle determinism, save/load roundtrip, idempotent replay, Warden legality sweep across ≥100 seeded states.
- **Smoke test** `tools/smoke.sh`: boots the server, drives a full match to victory via the API, asserts save + stats files, then replays a full match with chaos on and asserts completion; kills the server. Fully headless.

## 10. Constraints & non-goals
- Backend C++17 only; no Node/Python game logic, no WASM. Frontend JS talks to the API only.
- No deck builder, collection/economy, multiplayer, audio, or external art (canvas-drawn glyphs and typography only).
- ~25-minute agent budget: cut features before cutting invariants.

## 11. Acceptance criteria
- [ ] `./run.sh` builds and serves a match playable end-to-end.
- [ ] Draw/lumen/turn rules, Shelled, Surge, and Undertow behave as specified.
- [ ] Warden completes turns using only legal actions on both difficulties.
- [ ] Win and defeat reach a result screen; stats persist across restarts.
- [ ] Mid-match refresh and server restart both resume correctly from `match.json`.
- [ ] Lantern Flicker on: 503s occur, auto-retry recovers, no action double-applies, match completes.
- [ ] Unit tests pass; `tools/smoke.sh` passes headless.
- [ ] README gets a first-time player into a match in under a minute.

## 12. Uniqueness / anti-clone
Not a Hearthstone/Magic reskin: all UI copy, card names, and flavor use the keeper/tide lexicon. Forbidden: placeholder cards ("Card 1"), lorem ipsum, debug-rectangle UI, an "AI" that picks random actions, and a chaos toggle that is wired but never actually fails.

When done, print `DONE task_5: Card battler prototype` and start the next task immediately.

---

## Task 06 — Physics sandbox balls
**workdir:** `task_games_06`
**id:** `games_06_physics-sandbox-balls`
**seed (original):** Build a 2D physics sandbox with spawnable balls, gravity toggle, and collision counters (box2d or simple physics).
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "single_shot", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "low", "language_runtime": "rust", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "gaming", "ui_surface": "game_loop_window", "persistence": "sqlite", "testing_depth": "smoke_only", "novelty_hook": "domain twist: niche audience + unusual constraint", "delivery": "single_readme_run", "modality": "text_code"}
**Time budget (low):** finish within ~8 minutes / prefer ≤12 tool-heavy turns; thin MVP — few files, minimal polish, ship a runnable demo. Stop at a demoable MVP — do not keep polishing past the budget.

### Platform prompt (implement this)

# PLATFORM PROMPT — Pegfall Lab

## 1. Project Request / Product identity

**Pegfall Lab** is a tiny 2D physics sandbox in **Rust** for prototyping **pachinko-style boards** — I'm a solo dev building the tool I wanted while sketching cabinet layouts. You place pegs on a board, drop balls from a chute, flip gravity to stress-test the layout, and read **per-peg collision counters** to judge whether a board is "fair" or degenerate (one peg eating 80% of hits). It runs as a **real-time game-loop window**, not a plot or a log.

The unusual constraint that defines the product: **the simulation is fully deterministic and seeded**. Same seed + same peg layout + same drop pattern ⇒ identical trajectories and identical hit histograms, every run. The seed is always visible in the HUD. This is a measurement instrument, not a toy ball pit.

## 2. Target users & primary jobs-to-be-done

- **Indie pachinko/peggle-like designers** who need peg-hit distribution data before committing to a layout.
- **Marble-run / kinetic-sculpture hobbyists** who want to replay an interesting drop exactly.
- Jobs: sketch a layout fast → drop a seeded batch → read hit counts → tweak pegs → re-run the identical seed and compare → save the layout with its stats.

## 3. Core requirements / entities

- **Ball**: position, velocity, fixed radius, restitution; cap of **32 live balls** (oldest despawns past the cap).
- **Peg**: static circle with a persistent `hit_count`; board budget of **at most 64 pegs** ("cabinet spec").
- **Board bounds**: four walls with restitution; balls settle along the current gravity direction.
- **Run**: a seeded drop session; ends when the player presses record, producing a stored histogram.
- **Physics**: hand-rolled circle–circle impulse + positional correction, ball↔peg (static) and ball↔ball, **fixed timestep** (e.g. 120 Hz accumulator) so determinism holds. Do **not** pull in rapier/box2d — keep deps light (`macroquad` for the window, `rusqlite` bundled, nothing heavy).

## 4. Major feature areas

- **Spawn tools**: left-click places/selects a peg (right-click deletes); pressing **B** drops a ball from the top chute with seeded jitter; click-drag on empty space spawns a ball with the drag vector as initial velocity.
- **Gravity toggle**: **G** cycles Down → Up → Zero-G; HUD always shows current mode; existing balls keep momentum through the toggle.
- **Collision counters**: every ball↔peg contact increments that peg's counter; pegs are heat-tinted by hit count; **Tab** toggles numeric labels; HUD shows total hits and the current "hot peg" (id + %).
- **Determinism controls**: HUD displays seed; **N** reseeds; physics itself uses no RNG — only spawn jitter does (small inline xorshift, seeded).
- **Pause/resume** (Space), clear balls (**C**), reset all counters (**0**).
- **Persistence**: **F5** saves the layout (pegs + seed), **F9** reloads the latest layout, **R** ends and records the current run to SQLite.

## 5. Domain-specific workflows (happy path + edge cases)

Happy path: launch → place 20–40 pegs → press B repeatedly to drop a seeded batch → read heat map → Tab for exact counts → press R to store the run → G to Zero-G and watch drift behavior → F5 to save the board.

Edge cases to handle:
- Spawn overlapping a peg → reject with a brief red flash; no NaNs, no tunneling explosions.
- Zero-G drift → clamp ball speed to a sane max so nothing escapes bounds.
- Up gravity → balls settle on the ceiling; counters keep accumulating.
- Ball cap hit → oldest ball despawns cleanly (no counter corruption).
- Same seed dropped twice after **0** reset → identical final histogram (this is the product's core promise).

## 6. Data & persistence expectations

SQLite file `pegfall.db` in the working directory, auto-created. Tables: `layouts(id, name, seed, created_at, pegs_json)`, `runs(id, layout_id, seed, ticks, total_hits, histogram_json, created_at)`, `settings(key, value)` for gravity mode and label visibility. Layout autosaves on quit; settings restore on launch.

## 7. UX / API surface expectations

Readable HUD: seed, gravity mode, live ball count, peg count vs 64 budget, total hits, hot peg, and a compact controls line. Game-over isn't a thing here — but **run-recorded** and **layout-saved** toasts confirm persistence. Also provide a headless smoke mode: `cargo run -- --headless --seed 7 --ticks 600` runs the sim with no window and prints a summary (total hits, hot peg id, a simple checksum of final ball positions) so the demo is verifiable without a display.

## 8. Quality, security, and reliability expectations

Deterministic fixed-timestep sim; no panics on malformed SQLite file (recreate and warn); no unwraps in the hot loop; stays at interactive framerate with 32 balls + 64 pegs on modest hardware.

## 9. Documentation & testing expectations

- `cargo test` smoke suite only: circle-collision resolution sanity, spawn-overlap rejection, **determinism test** (two sims, same seed, equal final positions/histogram), SQLite round-trip of a layout.
- **README.md** is the single delivery doc: one-command run (`cargo run --release`), controls table, what determinism means here, headless verification command, known limitations.

## 10. Constraints & non-goals

Rust + `macroquad` window + `rusqlite`; no game engines, no rapier/box2d, no audio, no networking, no level-editor polish beyond click-place pegs, no assets beyond primitives. Few files, lean MVP — a runnable, measurable demo beats breadth.

## 11. Acceptance criteria

- [ ] Window opens into a live board; pegs placeable, balls spawnable, gravity cycles Down/Up/Zero-G.
- [ ] Per-peg collision counters increment, heat-tint, and show numeric labels on Tab; hot-peg readout correct.
- [ ] Headless run with a fixed seed twice yields identical summary/checksum.
- [ ] Layout save/load and run recording persist to SQLite and survive restart.
- [ ] `cargo test` passes (collision, spawn reject, determinism, db round-trip).
- [ ] README enables first session + headless verification in under 5 minutes.

## 12. Uniqueness / anti-clone constraints

Not a Breakout/Pong reskin, not a generic "ball pit demo," not a scored arcade game. Must use pachinko-cabinet vocabulary (peg, chute, board, run, histogram), treat **seeded determinism + per-peg hit analytics** as the product's reason to exist, and enforce the 64-peg / 32-ball cabinet budget visibly in the HUD. Placeholder UIs or non-deterministic physics are failures.

When done, print `DONE task_6: Physics sandbox balls` and start the next task immediately.

---

## Task 07 — Typing race multiplayer local
**workdir:** `task_games_07`
**id:** `games_07_typing-race-multiplayer-local`
**seed (original):** Create a local multiplayer typing race: shared prompt, per-player progress bars, WPM, and winner screen.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "medium", "language_runtime": "javascript", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "education", "ui_surface": "react_spa", "persistence": "localstorage", "testing_depth": "unit_light", "novelty_hook": "must include a live demo mode with sample data", "delivery": "docker_compose_optional", "modality": "text_code"}
**Time budget (medium):** finish within ~15 minutes / prefer ≤18 tool-heavy turns; solid MVP — core features + light tests, avoid gold-plating. Stop at a demoable MVP — do not keep polishing past the budget.

### Platform prompt (implement this)

# PLATFORM PROMPT — STATICLINE: Intercept Desk

## 1. Project Request / Product identity
Build **STATICLINE**, a local-multiplayer typing race set in a 1970s numbers-station listening post. 2–4 players are rival intercept operators transcribing the same burst transmission. The twist: races are **asynchronous ghost relays** — players run one at a time on the shared keyboard while previously recorded opponents replay as live "ghost" progress lanes, so everyone still races head-to-head on one machine. A built-in **Demo Desk** mode plays a full match between two recorded operators (sample data) with zero input.

Stack is locked: **JavaScript, React SPA, localStorage persistence**. No backend, no netcode. Docker Compose optional convenience only.

## 2. Target users & primary jobs-to-be-done
- A staff engineer demoing a side project: wants `npm install && npm run dev` playable in <2 minutes, plus logic tests they can trust.
- Small groups (game night, classroom warm-up) who want a fair one-keyboard race with a clear winner screen and rematch.
- Solo users who want to watch the Demo Desk or race a recorded ghost.

## 3. Core requirements / entities
- **PlayerProfile** `{ id, name, color }` — 2–4 per match, unique names enforced.
- **Transmission** `{ id, text, difficulty, lengthClass }` — themed prompts loaded from a data file (`src/data/transmissions.js`), at least 12 entries across short/standard/burst classes. No lorem ipsum.
- **KeystrokeLog** `[{ t, char, correct }]` — timestamped per run; powers ghost replay.
- **RaceRun** `{ playerId, transmissionId, elapsedMs, wpm, accuracy, progress, keystrokeLog, status: finished|forfeit|timeout }`.
- **Match** `{ id, seed, transmissionId, runs[], winnerId, createdAt }`.
- **Settings** `{ difficulty, lengthClass, ghostSpeed, muted, timeCapSec }`.

## 4. Major feature areas
- **Main menu**: New Match, Demo Desk, History, Settings. Cohesive retro-terminal styling (phosphor palette, scanline CSS), not debug rectangles.
- **Roster setup**: add/edit 2–4 operators, auto-assign colors, reject duplicate/blank names.
- **Race loop**: countdown → per-player run. During a run show: the shared transmission with per-character correct/error highlighting, the active operator's progress bar ("signal lock"), live WPM ("key rate"), accuracy ("fidelity"), elapsed timer, and **ghost lanes replaying earlier runs in real time**.
- **Scoring**: WPM = (correct chars / 5) / minutes; accuracy = correct keystrokes / total keystrokes. Backspace allowed; corrections count as keystrokes. Paste disabled. Runs end on completion, forfeit (Esc), or time cap.
- **Winner screen**: ranked table (finished runs by elapsed time; unfinished by progress, then accuracy), winner call-sign, per-run stats, Rematch (same seed) and New Transmission (reseed) buttons.
- **Demo Desk**: one click plays a full 2-operator match using shipped sample KeystrokeLogs with realistic WPM curves and injected typos; user can adjust ghost speed or quit to menu.
- **History**: last 10 matches from localStorage with winners and stats; clear-history control.
- **Settings**: difficulty, length class, ghost replay speed (0.5×/1×/2×), mute, time cap (45/60/90s).

## 5. Domain-specific workflows
**Happy path:** Menu → New Match → add 3 operators → pick standard length → seeded transmission dealt → P1 runs solo → P2 runs while P1's ghost replays → P3 runs against both ghosts → winner screen → rematch.
**Edge cases:** duplicate names blocked; empty roster blocks start; a forfeit run still replays as a partial ghost; timeout marks run `timeout` and ranks below finishers; exact elapsed-time tie broken by accuracy then WPM (deterministic); corrupt localStorage payload falls back to defaults without crashing; replaying a ghost at 2× never desyncs from its KeystrokeLog.

## 6. Data & persistence
localStorage only, versioned keys: `staticline:v1:profiles`, `staticline:v1:settings`, `staticline:v1:matches` (capped at 10), `staticline:v1:demoSeeded`. All reads validated; schema version mismatch triggers safe reset. Transmissions and demo ghost data ship as source data files, not storage.

## 7. UX / API surface expectations
- Single-page app, hash or state-based views: Menu, Setup, Race, Results, History, Settings.
- Controls documented on-screen and in README: typing advances, Backspace corrects, Esc forfeits, Enter confirms.
- HUD readable at a glance: progress bars per lane with operator color + name, live WPM/accuracy, transmission pane with error highlighting.
- Seeded RNG (e.g., mulberry32) for transmission selection so matches and tests are reproducible.

## 8. Quality, security, and reliability expectations
- Pure logic modules separated from components: `src/lib/scoring.js`, `src/lib/race.js` (ranking/winner), `src/lib/rng.js`, `src/lib/ghost.js` (position at time t), `src/lib/storage.js`.
- No eval, no dangerouslySetInnerHTML, no external network calls; all assets local.
- Ghost replay must be a pure function of `(keystrokeLog, elapsedMs)` — same inputs, same rendered position, always.

## 9. Documentation & testing expectations
- **Vitest** unit tests (light, no GUI tests) covering: WPM/accuracy math, winner ranking incl. tie-breaks and forfeits, seeded transmission pick determinism, ghost position at t (including beyond-log and 2× speed), storage validation/fallback.
- README: fantasy summary, controls, how the relay/ghost fairness works, run/test/build commands, design notes on scoring and replay determinism, known limitations.

## 10. Constraints & non-goals
- No accounts, no server, no real-time multiplayer netcode, no external prompt APIs.
- No heavy deps: React + Vite + Vitest only; no state-management library unless clearly justified.
- Docker Compose optional (`docker-compose.yml` for a static-serve of the build); `npm run dev` must work with zero Docker.
- No placeholder prompts, no generic typing-test clone copy.

## 11. Acceptance criteria
- [ ] App launches to a styled menu; a full 2–4 player relay match is playable end-to-end.
- [ ] Ghost lanes replay prior runs deterministically during subsequent runs.
- [ ] WPM, accuracy, and progress bars update live and match README formulas.
- [ ] Winner screen ranks correctly, handles forfeit/timeout/ties, offers rematch/reseed.
- [ ] Demo Desk plays a complete sample-data match with no keyboard input.
- [ ] Settings, profiles, and last-10 history persist across reload via versioned localStorage keys with safe fallback.
- [ ] `npm test` passes ≥ 12 unit assertions across the four logic modules.
- [ ] README enables a first play session without outside help.

## 12. Uniqueness / anti-clone constraints
- The async **ghost-relay on one keyboard** is the defining mechanic; do not substitute simultaneous-focus pseudo-multiplayer.
- Transmissions must be in-fiction (intercepted bursts, coordinates, code phrases), not lorem ipsum or quote-db dumps.
- Terminology stays diegetic in UI copy: operators, transmissions, signal lock, key rate, fidelity.
- No "Todo app" energy: any static, non-interactive, or placeholder-only screen is a failure condition.

When done, print `DONE task_7: Typing race multiplayer local` and start the next task immediately.

---

## Task 08 — Roguelike ASCII dungeon
**workdir:** `task_games_08`
**id:** `games_08_roguelike-ascii-dungeon`
**seed (original):** Implement a small ASCII roguelike: procedural rooms, fog of war, enemies, inventory of 3 items, and save.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "resume_mid_task", "repo_state": "partial_scaffold", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "gaming", "ui_surface": "html_canvas", "persistence": "memory_only", "testing_depth": "unit_plus_smoke", "novelty_hook": "offline-first; no cloud accounts", "delivery": "one_command_dev_server", "modality": "text_code"}
**Time budget (hard):** finish within ~25 minutes / prefer ≤25 tool-heavy turns; full PRD depth — richer acceptance criteria and verification. Stop at a demoable MVP — do not keep polishing past the budget.

### Platform prompt (implement this)

# Deepvault Survey — ASCII Salvage Roguelike

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

When done, print `DONE task_8: Roguelike ASCII dungeon` and start the next task immediately.

---

## Task 09 — Puzzle match-3 lite
**workdir:** `task_games_09`
**id:** `games_09_puzzle-match-3-lite`
**seed (original):** Build a match-3 puzzle lite with board swap, cascades, score targets, and limited moves.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "multi_turn_repair", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "gaming", "ui_surface": "desktop_window", "persistence": "json_file", "testing_depth": "integration_light", "novelty_hook": "accessibility-first keyboard UX", "delivery": "cli_entry_plus_ui", "modality": "text_code"}
**Time budget (low):** finish within ~8 minutes / prefer ≤12 tool-heavy turns; thin MVP — few files, minimal polish, ship a runnable demo. Stop at a demoable MVP — do not keep polishing past the budget.

### Platform prompt (implement this)

# Project Request — DockSort: Shift Quota

Build **DockSort: Shift Quota**, a Python 3.10+ desktop match-3 puzzle lite for
warehouse operations training demos. The player is a dock supervisor clearing a
grid of freight SKUs (crates, pallets, drums, coils, sacks) by swapping adjacent
tiles to line up 3+ of a kind, triggering cascades that feed a **shift quota**
(score target) before the **forklift battery** (move budget) runs out.

The defining constraint: **accessibility-first keyboard UX**. The entire game is
fully playable without a mouse. Every tile renders with both a color and a
distinct letter glyph (C/P/D/L/S) on a colorblind-safe palette, and a live text
log narrates each swap, match, and cascade in plain language.

**Stack lock:** Python 3.10+, stdlib `tkinter` desktop window, JSON file
persistence. No third-party dependencies. Thin MVP: ~5 files, runnable demo.

# Target users & primary jobs-to-be-done

- **Enterprise buyer (training-tools evaluator):** wants a 60-second demo that
  launches from a CLI, plays coherently, and proves deterministic logic.
- **Player (warehouse trainee):** wants a quick round with a clear quota, fair
  move budget, and keyboard-only control.

# Core requirements / entities

- `Tile` — SKU type (5 kinds), grid position, glyph letter.
- `Board` — 8×8 grid; seeded generation with **no starting matches** and at
  least one legal move guaranteed.
- `Cursor` — keyboard-navigable highlight; two-step swap (select, then direction).
- `Level` — seed, quota (score target), move budget, cascade multiplier rule.
- `RunState` — score, moves remaining, quota progress, outcome (win/lose).
- `SaveFile` — JSON: settings, best scores per level, last-run summary.

# Major feature areas

- **Core loop:** select tile → swap with adjacent → validate match; illegal
  swaps refund the move and bounce back. Matches clear, gravity drops tiles,
  refills spawn from seeded RNG, **cascades** resolve automatically with a
  rising multiplier (×1, ×2, ×3… per chain step).
- **Progression:** 3 config-driven levels in `levels.json` (rising quota,
  tighter move budget). Win = quota met before moves hit 0; lose = battery dead.
- **Accessibility layer (the twist):** full keyboard map (arrows = move cursor,
  Space = select/deselect, H = hint flashes one legal move, P = pause,
  R = restart, M = mute beeps, +/- = animation speed). High-contrast mode
  toggle (F1). Every event appends a sentence to an on-screen log panel
  ("Swap crate at B4 → 3 pallets matched, +90 pts, cascade ×2").
- **CLI entry:** `python main.py` launches the window;
  `python main.py --level 2 --seed 42`; `python main.py --smoke` runs the
  headless smoke (see Quality) and exits with a status code.
- **Meta:** main menu (level select via keyboard), win/lose screen with quota
  bar recap and restart, best-score table loaded from JSON.

# Domain-specific workflows

**Happy path:** launch → menu → pick level → swap tiles under quota pressure →
cascade chains push score past quota → win screen → best score persisted →
restart or next level.

**Edge cases:** swap with no match (refund move, log message); board with no
legal moves after a cascade (auto-reshuffle, same seed stream, logged); moves
exhausted mid-cascade (cascade finishes scoring before lose check); corrupt or
missing `save.json` (regenerate defaults, never crash).

# Data & persistence

- `save.json` in repo root: `{settings, best_scores, last_run}` — written on
  level end and on settings change; atomic-ish write (temp + rename).
- `levels.json`: level id, seed, quota, move budget, board size. Game logic must
  be reproducible from seed (documented RNG usage).

# UX / API surface expectations

- Window ~640×520: board left (tiles drawn as colored rounded rectangles with
  bold glyph letters — no image assets), right panel with quota bar, moves,
  score, and the scrolling text log.
- Controls overlay shown on the menu screen; README repeats it.
- Pure logic module (`board.py`) fully decoupled from tkinter: functions for
  `find_matches`, `apply_gravity`, `resolve_cascades`, `is_legal_swap`,
  `has_legal_move` — all deterministic given a seed.

# Quality, security, and reliability expectations

- No network, no eval, no file access beyond the two JSON files.
- Seeded RNG only; a given `--seed` reproduces the same board and refills.
- Game must launch and reach a playable state on a modest laptop; 8-minute
  agent budget means prefer simple, correct code over polish.

# Documentation & testing expectations

- `README.md`: run commands, full keyboard map, win/lose rules, seed
  reproduction note, known limitations.
- **Integration-light tests** (`tests/test_board.py`, stdlib `unittest`):
  seeded board has no initial matches; a scripted swap produces a match and
  correct score; gravity leaves no gaps; cascade multiplier accumulates; lose
  triggers at 0 moves.
- **Smoke (browser_smoke adapted to desktop):** `python main.py --smoke`
  instantiates the logic layer headless, plays a scripted sequence of legal
  swaps on level 1, asserts score > 0 and quota bookkeeping is consistent,
  writes `smoke_report.json`, exits 0/1. This is the verification entry point.

# Constraints & non-goals

- No third-party packages, no assets, no audio files (tkinter bell is fine).
- No mouse-only interactions anywhere; mouse clicks on tiles are optional
  sugar, never required.
- No animations beyond simple redraw flashes; no multiplayer, no accounts,
  no level editor, no online leaderboards.

# Acceptance criteria

- [ ] `python main.py` opens a playable keyboard-driven session in under 3s
- [ ] Swap/match/cascade/gravity loop works; illegal swaps refund the move
- [ ] Quota met → win screen; moves exhausted → lose screen; both offer restart
- [ ] Full game completable with keyboard only; glyphs visible on every tile;
  text log narrates events
- [ ] `save.json` persists settings and best scores; corrupt file self-heals
- [ ] `--seed N` reproduces identical boards across runs
- [ ] `python main.py --smoke` exits 0 and writes `smoke_report.json`
- [ ] `python -m unittest` passes the board logic tests
- [ ] README enables a first play session without reading source

# Uniqueness / anti-clone constraints

- **Not** a generic candy/gem clone: tiles are warehouse SKUs with glyph
  letters, score is a "shift quota," moves are a "forklift battery," and the
  log speaks freight language. No jewel/candy/bejeweled naming anywhere.
- The accessibility layer (glyphs, keyboard-only play, narrated log, F1
  contrast mode, hint key) is a shipped feature, not a README promise.
- No placeholder rectangles without glyphs, no hardcoded single level, no
  mouse-dependent UI, no "TODO" stubs in shipped paths.

When done, print `DONE task_9: Puzzle match-3 lite` and start the next task immediately.

---

## Task 10 — Simulated stock trading game
**workdir:** `task_games_10`
**id:** `games_10_simulated-stock-trading-game`
**seed (original):** Create a stock trading simulation game: fake price series, buy/sell portfolio, leaderboard of profit.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "visual_diff", "session_shape": "approval_gated", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "go", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "finance_fintech", "ui_surface": "static_html", "persistence": "sqlite", "testing_depth": "smoke_only", "novelty_hook": "deterministic --seed for reproducible runs", "delivery": "notebook_plus_script", "modality": "text_code"}
**Time budget (hard):** finish within ~25 minutes / prefer ≤25 tool-heavy turns; full PRD depth — richer acceptance criteria and verification. Stop at a demoable MVP — do not keep polishing past the budget.

### Platform prompt (implement this)

# PROJECT OBJECTIVE — SeedStreet Exchange

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

When done, print `DONE task_10: Simulated stock trading game` and start the next task immediately.

---
