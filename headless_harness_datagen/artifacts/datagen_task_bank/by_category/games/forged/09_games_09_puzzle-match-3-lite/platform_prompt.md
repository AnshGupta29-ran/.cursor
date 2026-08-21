# Project Request — DockSort: Shift Quota

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `desktop_window`
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
