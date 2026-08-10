# Rustwake: Core Rush — Design Notes

## Turn model

Sides alternate (Copperjacks first). At the start of a side's activation every
living unit on that side resets to 2 AP and `acted = false`. A unit may act in
any order:

- **Move** — 1 AP. Destination must be inside the unit's BFS movement range
  (4-neighborhood, budget = class move stat). Crates and containers block
  movement; occupied tiles block pathing.
- **Attack** — 1 AP, and sets `acted = true` (ends that unit's activation).
  Range is Manhattan distance. The target must be visible (see LOS).
- **Pick up core** — 1 AP, from a tile adjacent to (or on) the core.
- **Pass** — always available; a boxed-in unit just passes.

"End turn" flips sides; the match turn counter increments when the
Copperjacks' activation begins again. Turn 40 is the cap. Win checks run after
every mutating action: wipe check, core-extraction check (carrier standing on
their home row), then cap tiebreak (units alive → total HP → draw).

## Combat, cover, LOS

- Shot line: supercover walk between tile centers (Bresenham variant that
  records diagonal corner-crossing cells).
- Any intermediate `container` → shot blocked (`canShoot = false`, the UI says
  why).
- Any intermediate `crate` that is orthogonally adjacent to the **target** →
  half cover → hit chance 0.55 instead of 0.80. Spotters ignore half cover.
- `previewShot` is the single source of truth; both the hover preview and the
  resolution consume it, so preview and resolution can never disagree.
- Rolls use `Rng` (mulberry32) whose serializable state is `{seed, calls}`.
  Restore = re-seed + fast-forward `calls` draws. Both combat and AI
  tie-breaks draw from the same stream, so a saved match replays identically.

## Scrapbrain scoring

For each living unit, `scoreActions` enumerates candidates and assigns utility:

| Candidate | Scoring sketch |
| --- | --- |
| Attack in place | 30 + dmg·6 + chance·20; +50 vs the carrier; +25 if lethal |
| Move+attack | 24 + dmg·6 + chance·18; +45 vs the carrier; +22 if lethal; small cover bonus at the destination |
| Move (general) | 2 base; +6 per tile closed on the loose core; +7 per tile closed on an enemy carrier; +35 if the move enables a pickup |
| Carrier move | 40 + 8 per tile closed on home row; +1000 for stepping onto it (extraction wins) |
| Retreat (HP ≤ 2) | +5 per tile of distance from the nearest enemy |
| Cover-seeking | +0.6 per adjacent crate, +0.4 per adjacent container at the destination |
| Pickup in place | 45 |
| Pass | 1 (3 if HP ≤ 2) |

Selection: stable descending sort with a tiny seeded jitter for tie-breaks;
best action wins. **Easy** difficulty: with probability 0.15 the second-best
action is taken instead (the "blunder"). The same scorer drives the headless
smoke match for both sides.

Worker protocol: main thread posts `{state, unitId, rng}`; the worker runs
`decideForUnit` and returns `{action, rng}` (the updated RNG state keeps the
stream deterministic across the worker boundary). 2s timeout, one strike on
error → main-thread fallback + console warning.

## Log event schema

```jsonc
{
  "type": "attack",            // one of match_start, turn_start, move, attack,
                               // hit, miss, unit_down, core_pickup, core_drop, match_end
  "sessionId": "s_…",          // per browser profile
  "matchId":   "m_…",          // per match
  "turn":      7,               // match turn counter
  "ts":        1722440000000,  // epoch ms
  "data":      { "attacker": "a1", "target": "p2", "chance": 0.8 }
}
```

Events buffer in `localStorage` (`rustwake.logbuffer`, FIFO cap 200) and
batch-POST to `/logs`. The API validates shape (400 on junk, 256KB body cap,
≤500 events per batch), appends to `server/logs/events.jsonl`, and folds each
event into the `/metrics` counters.

## Persistence layout

| Key | `v` | Contents |
| --- | --- | --- |
| `rustwake.save` | 1 | Full `GameState` incl. `rng: {seed, calls}` — deleted when the match ends |
| `rustwake.settings` | 1 | `{telemetryOptOut, seenControls}` |
| `rustwake.history` | 1 | Last 10 `{matchId, mapId, difficulty, winner, turns, cause, seed, ts}` |
| `rustwake.logbuffer` | 1 | Pending events (cap 200) |

## Known limitations (MVP cuts)

- No animations; the AI turn is paced with short timeouts for readability.
- No path drawing — BFS highlights show reachable tiles, not the exact route.
- Spotter long-range shots through crate fields only get cover from crates
  adjacent to the target (per spec), not from mid-line crates.
- The API keeps counters in memory; restarting it resets `/metrics` (the
  JSONL log on disk is the durable record).
- Single difficulty knob (Easy blunder rate); Normal has no lookahead beyond
  the utility scores above.
- Desktop mouse-first; no touch support.
