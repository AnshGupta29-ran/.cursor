# Core Tap — Abyssal Survey Rig

A single-player Breakout/Arkanoid-style arcade game in Python 3.10+ / Pygame.
You pilot a deep-sea **survey rig** (paddle), reflecting a **sonar pulse**
(ball) to fracture **rock strata** (bricks) and extract ore across a chain of
drill sites (levels).

## Setup and first play (< 5 minutes)

```bash
pip install -r requirements.txt
python -m coretap            # play
python -m pytest -q          # tests (headless, no display needed)
python -m coretap.preview    # static preview build -> preview/*.png + index.html
```

Controls: **←/→ or A/D** move rig · **Space** launch pulse · **P/Esc** pause ·
**F5** export snapshot · **F9** import snapshot · **R** restart · **Esc** menu.

Win: fracture every destructible stratum across all three sites. A pulse lost
below the floor costs 1 hull; 3 hulls per run.

## Strata classes

| Glyph | Class    | Hits | Points | Notes                          |
|-------|----------|------|--------|--------------------------------|
| `s`   | sediment | 1    | 50     | filler rock                    |
| `o`   | ore      | 1    | 150    | 35% module drop rate           |
| `c`   | core     | 3    | 300    | visibly cracks as it weakens   |
| `b`   | basalt   | —    | 0      | indestructible blocker         |

Score = class points × site depth multiplier (site 1/2/3 = ×1.0/×1.5/×2.0).

Modules: `wide_rig`, `split_pulse` (multiball, max 3 pulses), `drag_field`
(slows pulses, 6 s), `pierce_charge` (pass-through, 5 s), `spare_hull` (+1
life). Timed modules **stack by refresh** — re-collecting resets the timer, it
never adds duration.

## Snapshot format spec (schema v1)

F5 writes `saves/snapshot_<slot>.json`; F9 restores it. Plain JSON, one object:

```json
{
  "version": 1,
  "game": "coretap",
  "site_index": 0,
  "score": 1200,
  "hulls": 3,
  "seed": 12345,
  "rng_state": [3, [<625 ints>], null],
  "state": "playing",
  "speed_bonus": 12.0,
  "rig_x": 450.0,
  "wide": false,
  "timers": {"drag_field": 4.2},
  "brick_bitmap": [{"cls": "sediment", "hits": 1}, ...],
  "pulses": [{"x": 1.0, "y": 2.0, "vx": 0.0, "vy": -360.0, "attached": false}],
  "drops": [{"kind": "ore", "x": 100.0, "y": 200.0}]
}
```

- `brick_bitmap` is row-major over the site's non-empty grid cells;
  `hits: 0` means the stratum is already fractured.
- `rng_state` is Python's `random.getstate()` serialized
  (`[version, [ints], gauss]`), so drop rolls resume exactly.
- Validation rejects unknown `version`, non-`coretap` payloads, wrong types,
  negative hulls, malformed RNG state — with a message naming the bad field.
  A rejected snapshot leaves the current run untouched.

## Persistence

All JSON, all writes atomic (tmp file + `os.replace`), all reads
schema-validated with a `version` field:

- `levels/site_01..03.json` — glyph grids (`s`/`o`/`c`/`b`/`.`), drop tables,
  `speed_ramp`. Malformed files raise a validation error naming file + field.
- `saves/highscores.json` — top-10 `{callsign, score, site}`; missing/corrupt
  regenerates empty, never crashes.
- `saves/settings.json` — `difficulty`, `mute`, `game_speed`.
- Settings and leaderboard are flushed on exit, including window close mid-run.

## Design notes (invariants & tradeoffs)

- **Fixed timestep** (1/60 s): physics is deterministic per platform; render
  decouples from simulation.
- **Swept collision**: each pulse sub-steps so no sub-step exceeds the pulse
  radius. At the hard speed cap (720 px/s) a pulse moves 12 px per tick —
  sub-stepping to ≤7 px makes brick tunneling impossible. Tradeoff: up to ~2
  sub-steps per tick at cap; trivial cost for ~50 bricks.
- **Reflection**: angle is linear in paddle impact offset, clamped to
  ±65° off vertical, speed preserved exactly (re-normalized after the bounce).
- **Speed ramp**: +6 px/s per fractured brick, hard cap 720 px/s; `drag_field`
  multiplies the *target* speed, so it also reduces the cap effectively.
- **Refresh-stacking**: timers are `dict[kind, seconds_left]`; applying a
  module assigns, never adds. One-line invariant, one-line test.
- **Seeded RNG per run**: one `random.Random(seed)` instance drives launch
  jitter and all drop rolls; its full state lives in the snapshot, making
  export → import bit-exact (covered by a deep-equality test).
- **Pure core / render split**: `coretap/core/` has zero pygame imports
  (physics, scoring, drops, snapshot codec, level loader); `coretap/render/`
  is drawing only. Tests exercise the core with no display.
- **Graceful degradation**: SDL dummy video/audio let tests and
  `python -m coretap.preview` run headless; if the audio mixer fails to init,
  the game runs silently.

## Known limitations

- Single snapshot slot (F5/F9 → `snapshot_1.json`); schema supports more.
- Difficulty setting is persisted but only `game_speed` affects play.
- Audio is square-wave beeps generated at boot; no music.
- Autopilot in the preview is deliberately simple (tracks lowest pulse).
