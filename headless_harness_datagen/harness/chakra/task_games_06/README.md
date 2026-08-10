# Pegfall Lab

A tiny 2D physics sandbox for prototyping **pachinko-style boards** — place pegs,
drop balls, flip gravity, and read per-peg collision counters.

**Stack:** Python 3 + pygame + sqlite3 (stdlib). Hand-rolled circle physics.
Fixed-timestep accumulator (120 Hz) for seeded determinism.

## Core promise

Same seed + same layout + same drop pattern ⇒ identical trajectories and identical
hit histograms, every run. The seed is always visible in the HUD.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| Left-click empty space | Place a peg |
| Left-click drag (empty space) | Spawn ball with drag velocity |
| Left-click on peg | Select peg |
| Right-click on peg | Delete peg |
| **B** | Drop ball from top chute (seeded jitter) |
| **G** | Cycle gravity: Down → Up → Zero-G |
| **N** | Reseed RNG (new random seed) |
| **Space** | Pause / resume physics |
| **C** | Clear all balls |
| **0** | Reset all peg hit counters |
| **Tab** | Toggle numeric hit-count labels on pegs |
| **F5** | Save layout + seed to SQLite |
| **F9** | Load latest layout from SQLite |
| **R** | Record current run to SQLite (clears balls & counters) |
| **Esc** | Quit (autosaves layout) |

## Headless verification

```bash
python main.py --headless --seed 7 --ticks 600
```

Running twice with the same seed produces identical output:

```bash
python main.py --headless --seed 7 --ticks 600 > out1.txt
python main.py --headless --seed 7 --ticks 600 > out2.txt
diff out1.txt out2.txt   # no diff
```

## Run tests

```bash
python test_smoke.py
```

Tests cover: collision sanity, spawn overlap rejection, 32-ball / 64-peg budget,
determinism (same seed → same histogram), SQLite layout round-trip, gravity
cycling, reseeding, hot-peg calculation, and headless idempotency.

## Persistence

`pegfall.db` auto-created in the working directory with three tables:
- `layouts` — saved peg layouts (name, seed, pegs_json)
- `runs` — recorded runs (seed, ticks, total_hits, histogram_json)
- `settings` — gravity mode, label visibility

## Budget

- **Max 64 pegs** ("cabinet spec")
- **Max 32 live balls** (oldest despawns past cap)
- **Zero-G** speed clamped to 300 px/s

## Known limitations

- No audio, no assets beyond primitives
- No Box2D/pymunk — hand-rolled circle physics
- Layout save/load stores positions and hit counts, not ball state
