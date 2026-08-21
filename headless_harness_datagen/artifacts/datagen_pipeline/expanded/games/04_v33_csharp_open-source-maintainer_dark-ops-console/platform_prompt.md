# VARIANT v33_csharp_open-source-maintainer_dark-ops-console - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `csharp`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `dark_ops_console`
- **ui_surface**: `static_html`
- **persistence**: `csv_files`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `csharp`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v33_csharp_open-source-maintainer_dark-ops-console`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v33_csharp_open-source-maintainer_dark-ops-console` when demoable.

---

## BASE PRD (honor unless mutated above)

# Fathom Fields — Deduction-First Harbor Sweeping (PRD)

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `csharp`
- **ui_surface:** `desktop_window`
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
