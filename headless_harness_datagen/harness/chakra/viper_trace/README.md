# Viper Trace — A* Snake Observatory

A Python + Pygame Snake game with two souls: a tight manual arcade mode and an
AI mode where the **Trace Engine** — a survival-aware A* planner — pilots the
snake and renders its thinking live on the grid.

## Setup

Requires Python 3.10+.

```bash
pip install pygame
```

## Run

```bash
python -m viper_trace                    # launch to the start menu
python -m viper_trace --mode ai          # skip menu, straight into AI mode
python -m viper_trace --mode manual --difficulty viper
python -m viper_trace --seed 42          # deterministic food sequence
```

## Controls

| Key | Action |
| --- | --- |
| Arrow keys / WASD | Steer (manual mode) |
| Up/Down (menu) | Select mode |
| Left/Right (menu) | Switch difficulty |
| Enter / Space (menu) | Start |
| `+` / `-` | Live speed adjust (within difficulty bounds) |
| `P` | Pause / resume |
| `T` | Toggle explored-cells tint (AI mode) |
| `R` | Restart run (in-game or from game over) |
| `Esc` | Back to menu / quit run |

## Difficulties

| Preset | Grid | Start speed | Obstacles | Score x |
| --- | --- | --- | --- | --- |
| Hatchling | 20×20 | 8 | border walls only | 1 |
| Viper | 30×25 | 10 | border + one internal wall | 2 |
| Apex | 40×30 | 12 | border + two internal walls | 3 |

Presets live in `viper_trace/config.py` — grid size, speed bounds, obstacle
layouts, and score multipliers are pure config data.

## The Trace Engine (AI mode)

Every tick the engine decides a route through three stages:

1. **A\* search** — 4-neighborhood, Manhattan heuristic, over free cells
   (walls, obstacles, and the snake's own body are blocked; the tail cell is
   treated as free since it vacates). Ties break deterministically (fixed
   N, E, S, W expansion + insertion order), so runs are reproducible.
2. **Survival gate** — before committing, the engine *simulates the meal*:
   it advances the snake along the candidate path, grows once, then checks
   (BFS) that the post-meal head can still reach its own tail. A route that
   would trap the snake is rejected even though it reaches the food.
3. **Survival wander (fallback)** — when no safe route exists, the engine
   evaluates every legal move with a flood fill and picks the one maximizing
   reachable free area, preferring moves that keep the tail reachable. It
   never picks a lethal move while a survivable one exists.

The HUD reports the engine's state in its own language:

- `TRACE: SAFE ROUTE` — committed A* path (drawn as an amber line, head→food)
- `TRACE: SURVIVAL WANDER` — fallback active (path drawn red)
- `TRACE: NO PATH` — no legal move remains

The committed path is always drawn; the **explored-set tint** (last search's
A* closed set) toggles with `T`. Replanning happens once per tick and once
per meal; on the largest grid (40×30 = 1200 cells) each replan is a bounded
A* + one BFS + at most four flood fills, comfortably real-time.

## Persistence

Best scores per difficulty+mode, last speed per difficulty, last difficulty,
and the overlay toggle persist to `viper_trace/data/*.json` across runs.

## Determinism

`--seed N` seeds the food RNG per difficulty, so the same seed reproduces the
identical food sequence (and, in AI mode, the identical game) every time.

## Development

```bash
pip install pytest
python -m pytest viper_trace/tests/     # headless logic + render smoke suite
python -m viper_trace.smoke 42          # fast smoke: seed-42 AI run, score > 0
```

Logic (grid, snake, A*, survival gate, fallback, engine) is pure Python in
`viper_trace/` with no Pygame imports; only `game.py` renders.
