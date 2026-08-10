# Rustwake: Core Rush

A turn-based tactics skirmish in a junkyard. A hauler went down mid-yard and its
**power core** is still hot. Two salvage crews want it: you command the
**Copperjacks**; the computer runs the **Ferroscouts** (an AI called
*Scrapbrain*). Drag the core back to your extraction row — or just scrap the
whole rival crew.

- **Board:** 12×9 grid of open ground, crates, containers, and the core pad.
- **Win (two live paths):** wipe the enemy crew **or** carry the core onto your
  home extraction row (Copperjacks: bottom row, copper tint; Ferroscouts: top
  row, teal tint).
- **Match length:** 5–10 minutes, hard turn cap of 40.

## Run it

```bash
npm install
npm run dev      # opens the game at http://localhost:5173
```

Optional observability API (structured logs in, metrics out — the game plays
fine without it):

```bash
npm run api      # http://localhost:8787  (GET /health, GET /metrics, POST /logs)
```

Checks:

```bash
npm run test     # vitest unit tests (rules, RNG, LOS, cover, AI sanity)
npm run smoke    # boots the API, asserts endpoints, plays a scripted headless match
npm run build    # production build of the client into dist/
```

## Controls

| Input | Action |
| --- | --- |
| Click a Copperjack | Select unit |
| Click a blue-highlighted tile | Move (1 AP) |
| Click a Ferroscout | Shoot — dashed preview shows hit % and cover (1 AP, ends that unit) |
| Click the core tile while adjacent (or standing on it) | Grab the core (1 AP) |
| `Esc` | Deselect |
| `Enter` | End turn |
| `P` | Pause |

A first-run overlay explains all of this in-game; it shows once and is
remembered. Mid-match reload is safe: the menu offers **Resume Match** with the
exact board, AP, core position, turn, and RNG stream restored.

## The crews

| Class | HP | Move | Range | Damage | Notes |
| --- | --- | --- | --- | --- | --- |
| **Bruiser** | 10 | 3 | 1 (melee) | 4 | Slow anvil. Hits like a truck axle. |
| **Runner** | 6 | 5 | 2 | 2 | Natural core-carrier — fastest legs in the yard. |
| **Spotter** | 5 | 3 | 5 | 3 | Ignores half-cover penalties (sees right over crates). |

Each unit gets **2 action points** per side-turn. Moving costs 1 AP. Attacking
costs 1 AP and ends that unit's activation. Grabbing the core costs 1 AP from an
adjacent tile. A defeated carrier drops the core on the nearest open adjacent
tile. End turn is always available, even when boxed in.

## Combat and cover, in plain language

- Base hit chance is **80%**.
- If a **crate** sits adjacent to the target *and* the shot line crosses it,
  the target has half cover: hit chance drops to **55%**. Spotters ignore this.
- A **container** anywhere on the shot line blocks the shot completely — no
  roll, no preview, the game tells you it's blocked.
- Damage is fixed per class (see table). There is no armor, no crits.
- Before you confirm a shot, hovering an enemy shows a dashed line with the
  exact hit % and damage; the resolution uses the same math, so the preview
  always matches the outcome distribution.
- Every roll comes from a **seeded PRNG** (mulberry32). The seed is shown on
  the HUD and the result screen; replaying a seed reproduces the same combat
  stream.

## Turn cap and tiebreaks

Turn 40 is the last. If nobody has won by then: the crew with **more units
standing** wins; on a tie, **higher total HP** wins; still tied — a draw.
There is always a definite result.

## Persistence

Everything lives in `localStorage`, versioned:

- `rustwake.save` — full mid-match state including RNG seed *and* stream
  position (this is what powers Resume Match).
- `rustwake.settings` — telemetry opt-out, controls-overlay seen flag.
- `rustwake.history` — last 10 match results.
- `rustwake.logbuffer` — capped FIFO (200) of structured log events awaiting
  upload.

## Observability

The game emits structured JSON events (`match_start`, `turn_start`, `move`,
`attack`, `hit`, `miss`, `unit_down`, `core_pickup`, `core_drop`, `match_end`)
with session id, match id, turn, and timestamp. They buffer locally and
batch-POST to `http://localhost:8787/logs`. If the API is down, the buffer just
grows (capped at 200) and the game never blocks; it flushes when the API
returns. The telemetry opt-out checkbox on the menu is honored immediately.

The API is dependency-free Node (`server/api.mjs`, stdlib `http` only — plain
ESM with JSDoc types so it runs with zero build step; `RUSTWAKE_PORT` overrides
the default 8787). It appends every accepted batch to `server/logs/events.jsonl`
and serves live counters from `/metrics`: uptime, matches started/completed,
wins per side, turns played, attacks, hits, average turns per match, and total
log events received. Junk bodies get a 400.

## The AI

Scrapbrain is a documented utility scorer (see `DESIGN.md`), not random: for
each unit it scores candidate attacks, core grabs, carrier hunts, cover-seeking
moves, and retreats, then picks the best with seeded tie-breaks. It runs in a
Web Worker with a 2-second timeout; on any worker failure the game falls back
to main-thread scoring and logs a warning. On **Easy**, 15% of decisions take
the *second*-best action, which is measurably sloppier.
