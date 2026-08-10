# Tidewatch — Design Reference

This document is the authoritative description of the game's systems: the tide state
machine, movement-class rules, economy math, upgrade branches, boss behavior, difficulty
presets, and the save schema + versioning policy. All content is data-driven; this file is
the schema reference for adding towers, enemies, levels, and difficulties without code.

---

## 1. Architecture

Two layers, cleanly separated:

- **`Tidewatch.Core`** (`Assets/Scripts/Core`, `noEngineReferences: true`) — the pure C#
  simulation: grid, tide, pathfinding, waves, economy, upgrades, combat, save schema. No
  `UnityEngine` dependency, so it is deterministic given a run seed and unit-testable in
  EditMode. The Game layer feeds it `dt` and renders its state.
- **`Tidewatch.Game`** (`Assets/Scripts/Game`) — MonoBehaviours: a runtime bootstrap that
  builds the whole game from one scene, the grid/tower/enemy views (primitives), the HUD +
  screens, and procedural audio. Loads content from JSON in `StreamingAssets/Content`.

Determinism: all gameplay RNG flows through an injected `SeededRng` (xorshift128+). No bare
`UnityEngine.Random` in gameplay logic. A run is reproducible from its `runSeed`; the RNG
state is serialized into the save.

---

## 2. The Tide System (state machine)

The Tide Meter cycles on a **per-level schedule** — a repeating list of
`(phase, seconds)` pairs, scaled by the difficulty's `tideCadenceMult`.

```
        ┌──────────────────────────────────────────┐
        ▼                                          │
     [Low] ──→ [Rising] ──→ [High] ──→ [Ebbing] ──┘
```

- `Low` / `Rising` / `High` / `Ebbing` are the four phases (`TidePhase`).
- On each **turn** the sim: applies flood/drain to every tile, recomputes all path fields,
  and re-paths every living enemy **within the same simulation tick** (no teleporting, no
  soft-locks). A `OnTideTurn` event drives the water-rise animation and a surge sting.
- A **Tide-turn warning banner** appears 5 seconds ahead; the HUD shows phase + time-to-turn.

### Tile flood rules
| Terrain | Low | Rising | High | Ebbing | Notes |
|---|---|---|---|---|---|
| Causeway | dry | dry | **water** | dry | floods only at High |
| Trench | **dry** | water | water | water | drains only at Low |
| Deep Water | water | water | water | water | always water; pelagic-only |
| Rock | — | — | — | — | never walkable |
| Build Plot | — | — | — | — | never walkable; buildable |
| Gate / Base | walkable | walkable | walkable | walkable | path endpoints |

### Movement-class rules (who can be on a tile)
| Class | Dry tile | Water tile | Deep water | Effect of drying |
|---|---|---|---|---|
| Terrestrial | ✓ | ✗ | ✗ | If surrounded by water: slowed (never stuck) |
| Amphibious | ✓ | ✓ | ✗ | none |
| Pelagic | ✗ | ✓ | ✓ | **Beached** on a dry tile |

**Beached:** a pelagic enemy on a tile that has dried (or that it was caught on when the
tide turned) is slowed to 40% speed and takes **bonus damage from Flare Mortars**
(`bonusVsBeached`, default 2×). It recovers the moment its tile refloods.

**Shrouded:** deep-water Lurkers are Shrouded. A Shrouded enemy **cannot be targeted by
direct-fire towers** unless it is **illuminated** — inside a light tower's illumination
radius or the Lantern's built-in aura. Towers drop a target that leaves illumination
mid-volley. (Flare Mortar briefly illuminates its impact zone; the Fog Bell's Lantern
Chorus capstone reveals within its radius.)

---

## 3. Pathfinding

Per movement class, a **BFS distance field** is computed backwards from the Lantern over
the *current* walkability graph (O(W·H) per recompute). Enemies walk "downhill" to the
base. Because a field covers the whole map, multiple gates and multiple lanes are handled
uniformly and every enemy gets a next step without a per-enemy A*. Fields are recomputed on
every tide turn (towers sit on build plots, which are never walkable, so building does not
change the graph). An enemy whose current tile becomes unreachable keeps its last path if
still valid, otherwise is slowed — it never teleports and never soft-locks.

---

## 4. Economy

| Source | Formula |
|---|---|
| Kill bounty | `max(1, floor(enemy.bounty × difficulty.bountyMult))` |
| Wave-completion bonus | flat `30` Salvage |
| Early-call bonus | `min(50, floor(remainingScheduledSeconds × 2))` |
| Sell refund | `floor(totalInvested × 0.70)` |
| **Keeper's Reserve** | `min(40, floor(unspentSalvage × 0.04))` at each wave clear |

**Keeper's Reserve (thrift vs. spend):** at each wave clear you earn a **+4% dividend** on
*unspent* Salvage, hard-capped at **40**. The cap is the design fulcrum — it lets a frugal
Keeper smooth out a lean wave, but ensures hoarding can never out-earn simply building a
defense. The HUD shows a live preview of the next dividend so the tension is always visible.

All economy constants are exposed on the `Economy` class and set per difficulty.

---

## 5. Towers & upgrade branches

Every tower has 3 tiers. Tiers 1→2 are linear stat improvements; **tier 3 is a branch
choice between two mutually exclusive capstones** (pick one, the other is locked out).
All stats, costs, and branch effects live in `Content/towers.json`.

| Tower | Behavior | Capstone A | Capstone B |
|---|---|---|---|
| **Beacon Spire** | Beam that ramps damage the longer it holds a target; emits light | **Solar Lance** — burst window after 3s hold | **Dusk Beam** — beam also slows on hit |
| **Flare Mortar** | Lobbed AoE; illuminates impact; bonus vs Beached | **Star Shell** — +dmg, bigger flare | **Rapid Battery** — +fire rate |
| **Prism Array** | Chain-light arcing between enemies; +1 arc per adjacent Prism (resonance) | **Storm Lattice** — +2 arcs | **Focused Lens** — +dmg, −1 arc |
| **Harpoon Ballista** | Fast bolt piercing a line; cannot hit Shrouded | **Twin Cables** — +fire rate | **Broadhead** — +pierce, +dmg |
| **Fog Bell** | Support; pulses slow in radius, no damage | **Cracking Tone** — adds armor shred | **Lantern Chorus** — reveals Shrouded |

Targeting priority is selectable per tower: **First** (furthest along route), **Last**,
**Strongest** (highest HP), **Closest**.

---

## 6. Enemies

| Enemy | Class | HP | Speed | Armor | Bounty | Leak | Traits |
|---|---|---|---|---|---|---|---|
| Skitterling Shoal | Terrestrial | 20 | 1.6 | 0 | 6 | 1 | spawned in packs |
| Brine Hulk | Terrestrial | 180 | 0.55 | 4 | 22 | 3 | armored |
| Abyssal Lurker | Pelagic | 90 | 1.0 | 1 | 18 | 2 | **Shrouded** |
| Spitter | Terrestrial | 70 | 0.9 | 0 | 16 | 2 | disables a tower 3s every 5s |
| Broodmother | Amphibious | 320 | 0.6 | 2 | 40 | 5 | splits into 4 Skitterlings on death |
| **The Drowned Bell** (boss) | Amphibious | 4000 | 0.35 | 6 | 400 | 10 | **Tidecall** every 12s forces a tide surge; escorts spawn |

Damage is `max(1, raw − (armor − armorShred))`, then multiplied by `bonusVsBeached` for
Flare Mortars vs Beached targets. The boss's Tidecall calls `Tide.ForceSurge()`, advancing
the tide immediately — it can strand its own escorts or open new lanes mid-fight.

---

## 7. Difficulty presets

| Parameter | Calm Sea | Rising Gale | Abyssal Night |
|---|---|---|---|
| Enemy HP × | 0.85 | 1.00 | 1.30 |
| Enemy speed × | 0.90 | 1.00 | 1.10 |
| Bounty × | 1.10 | 1.00 | 0.90 |
| Starting Salvage | 260 | 200 | 160 |
| Lantern Light | 25 | 20 | 15 |
| Tide cadence × (higher = slower) | 1.20 | 1.00 | 0.80 |
| Leak damage × | 1.00 | 1.00 | 1.25 |

Difficulty is chosen per level; best clear (wave reached, clear time) is recorded per
(level, difficulty) pair.

---

## 8. Campaign levels

Four shipped levels, each a distinct tactical problem (not the same layout with bigger numbers):

1. **First Light** — a single causeway; teaches towers and the basic tide rhythm.
2. **The Drowning Shortcut** — two gates; at High tide the central causeway floods and a
   shorter trench route opens, rewriting the path mid-run.
3. **Where the Lurkers Swim** — deep trenches ring the Lantern; pelagic Lurkers in force
   force an investment in illumination.
4. **The Drowned Bell Tolls** — everything plus the boss, whose Tidecall surges the tide on
   its own schedule.

Clearing a level unlocks the next, plus that level's **Endless Night** mode (deterministically
scaled waves generated from the run seed).

---

## 9. Save schema & versioning

Three file types in `Application.persistentDataPath`: run slots (`run_slotN.json`), meta
progress (`meta.json`), settings (`settings.json`). All carry a `version` field
(`SaveSchema.CurrentVersion = 1`). Writes are atomic (write `.tmp`, delete target, rename).

**RunSave (v1)** — written at wave boundaries:
```
version, runSeed, rngS0, rngS1,
levelId, difficultyId, waveIndex, tideIndex, tideClock,
salvage, lanternLight, endless,
towers[]: { defId, x, y, tier, branchId, priority, totalInvested, disabledTimer },
leaks, salvageEarned, towersBuilt, elapsed
```

**Versioning policy:** the loader accepts only `CurrentVersion`. A file that is missing,
unparseable, or a different version is reported and the caller falls back to a fresh run —
it never crashes. When the schema changes, bump `CurrentVersion` and (optionally) write a
migration; the policy intentionally prefers a clean fresh-run fallback over risky migrations
for a save system that only spans one level's run.

---

## 10. Content schemas (add content with zero C# changes)

**Level (`Content/Levels/*.json`)** — discovered by scanning the directory:
```jsonc
{
  "id": "level_05",
  "displayName": "…",
  "briefing": "…",
  "expectedEnemies": ["skitterling", "…"],
  "parTimeSeconds": 600,
  "tideSchedule": [ { "phase": "Low|Rising|High|Ebbing", "seconds": 30 }, … ],
  "grid": [ "~~~~", "~CG", "…" ],   // rows top→bottom; legend ~ . C T # G B
  "waves": [ { "varianceSeed": 0,
    "entries": [ { "enemyId": "skitterling", "count": 8, "interval": 0.8,
                   "gate": 0, "delay": 0 } ] } ]
}
```
Waves are validated on load (unknown enemy ids, zero counts, bad gate indices are logged as
errors). Grid legend: `~` deep water · `.` rock · `C` causeway · `T` trench · `#` build
plot · `G` gate · `B` base.

**Tower (`Content/towers.json`)**, **Enemy (`Content/enemies.json`)**, **Difficulty
(`Content/difficulties.json`)** follow the DTO fields in `ContentLoader.cs`. All numeric
balance lives here.

---

## 11. Determinism & performance

- Simulation is deterministic given `runSeed`; wave variance and any rolls use the injected
  `SeededRng`. RNG state is saved and restored.
- Target: 60 fps at 1080p with ~150 live enemies and ~40 towers. The combat hot path avoids
  per-frame allocations: reused buffers (`_buffer`), no LINQ in per-tick loops, pooled
  spawn schedules. Enemy/tower views are cheap primitives with no per-frame `Instantiate`
  (spawn/despawn only on events).
