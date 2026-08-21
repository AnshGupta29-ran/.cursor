# VARIANT v27_csharp_enterprise-buyer_feature-flag-gates - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `csharp`
- **user_persona**: `enterprise_buyer`
- **novelty_hook**: `feature_flag_gates`
- **ui_surface**: `cli_tui`
- **persistence**: `json_file`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `csharp`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v27_csharp_enterprise-buyer_feature-flag-gates`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v27_csharp_enterprise-buyer_feature-flag-gates` when demoable.

---

## BASE PRD (honor unless mutated above)

# PLATFORM PROMPT — Pegfall Lab

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `rust`
- **ui_surface:** `static_html`
- **persistence:** `sqlite`
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
