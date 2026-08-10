# Tidewatch: Lantern of the Shattered Coast

A single-player tower defense game in **Unity (2022.3 LTS) + C#**. You are the Keeper of
the last tidal lighthouse-city on a drowned coastline. Each night, abyssal creatures surge
inland with the tide to extinguish the Great Lantern. Build lantern-tech and harpoon towers
on raised plots, hold the line through the waves, and keep the Lantern lit until dawn.

The signature system is the **Tide**: every level sits on a tidal flat and a visible Tide
Meter cycles Low → Rising → High → Ebbing on a per-level schedule. Tiles flood and drain
with the tide, so **the enemy path graph rewrites itself mid-run** and living enemies
re-path on the turn. Pelagic enemies caught on a drying tile become **Beached** (slowed,
and take bonus damage from Flare Mortars). Deep-water **Lurkers are Shrouded** and cannot
be targeted by direct-fire towers unless illuminated by a light tower or the Lantern's aura.

---

## Open & Run

1. Install **Unity 2022.3 LTS** (any `2022.3.x`) via Unity Hub.
2. **Add project from disk** → select this `Tidewatch/` folder.
3. Open the scene `Assets/Scenes/Game.unity`.
4. Press **Play**. Everything (content, UI, audio) is generated at runtime from the data in
   `Assets/StreamingAssets/Content/` — no other setup is required.

There is exactly **one scene** and one bootstrap `MonoBehaviour`; the game builds itself.

### Build a standalone player
`File → Build Settings → Add Open Scenes` → pick a platform (Windows/Mac/Linux) → **Build**.

---

## How to play

**Goal:** survive every wave with Lantern Light above zero. Defeat when Lantern Light
reaches 0. Victory when the final wave is cleared with the Lantern still lit.

### Controls / hotkeys
| Input | Action |
|---|---|
| `1`–`5` | Select a tower to build (Beacon Spire, Flare Mortar, Prism Array, Harpoon Ballista, Fog Bell) |
| Left click | Place selected tower on a raised plot / select a placed tower |
| Right click / `Esc` | Cancel placement (with a tower selected: deselect; otherwise: pause) |
| `Space` | Call the next wave (call early for a Salvage bonus) |
| `1×`/`2×` button | Toggle game speed |
| `☰` button | Pause menu (save, settings, abandon) |

### The loop
Build phase → call wave → towers auto-acquire targets (set each tower's priority: First /
Last / Strongest / Closest in its inspector) → enemies path toward the Lantern over the
*current* tide → kills earn Salvage → wave clears → **Keeper's Reserve** pays interest on
unspent Salvage → build/upgrade/sell → next wave. Watch the **Tide Meter** — a banner warns
5 seconds before the tide turns and rewrites the map.

### Economy
- **Salvage** from kills and wave-completion bonuses. Towers sell back at **70%**.
- **Keeper's Reserve:** at each wave clear you earn a capped **+4%** interest dividend on
  unspent Salvage. Hoarding pays, but unbuilt towers deal no damage — spend vs. save is
  the core tension (see `docs/DESIGN.md`).
- **Early-call bonus** for starting a wave before its schedule finishes.

### Towers (3 tiers each; tier 3 is a branch between two capstones)
Beacon Spire (ramping beam + light), Flare Mortar (AoE + bonus vs Beached), Prism Array
(chain-light, +1 arc per adjacent Prism), Harpoon Ballista (piercing line), Fog Bell
(slow/support). All stats live in `Assets/StreamingAssets/Content/towers.json`.

---

## Add content with **zero C# changes**

Everything is data in `Assets/StreamingAssets/Content/` as JSON:

- **New tower / enemy:** add an entry to `towers.json` / `enemies.json` (schema in
  `docs/DESIGN.md`).
- **New level:** drop a `level_XX.json` into `Content/Levels/`. It is discovered
  automatically at startup, gets a tide schedule, an ASCII tile grid, and a wave list, and
  appears in Level Select. The grid legend:
  `~` deep water · `.` rock · `C` causeway · `T` trench · `#` build plot · `G` gate · `B` base.
- **New difficulty:** add to `difficulties.json`.
- **Balance pass:** edit numbers in the JSON — no recompile of game code needed.

---

## Save / Load

- Full run saves at **wave boundaries** (the sanctioned simplification — a run is saved the
  moment a wave is cleared, and when you choose *Save Run* from the pause menu). **3 slots.**
- Saves store: run seed, level, difficulty, wave index, tide phase + clock, Salvage,
  Lantern Light, and every tower (plot, tier, branch, targeting, disable timer).
- Save files carry a **version number**; corrupted or older-version saves are detected,
  reported, and the game falls back to a fresh run instead of crashing. Writes are atomic
  (temp file + rename). Meta progress (unlocks, per-difficulty records) and settings are in
  separate files. All under `Application.persistentDataPath`.

---

## Tests

EditMode tests (Unity Test Framework) cover the pure simulation layer — no scene loading,
no timing dependencies:

`Window → Test Runner → EditMode → Run All`

Covers: pathfinding incl. a tide-flip re-path, wave-list validation (bad ids, zero counts),
economy (bounty, interest cap, sell refund), upgrade/branch application, tide progression +
Beached transitions, boss Tidecall, shroud targeting, defeat precedence, and save round-trip.

The simulation (`Assets/Scripts/Core`) is engine-free C# (`noEngineReferences`), so it is
deterministic given a run seed and unit-testable in isolation.

---

## Known limitations

- **Wave-boundary saves only** — no mid-wave full-state serialization (by design).
- Art is primitive-based (cubes/spheres/quads) and audio is procedurally synthesized —
  cohesive but intentionally minimal, per the brief.
- The Drowned Bell boss reuses the standard enemy renderer (a larger primitive), not a
  bespoke model.
- Flare Mortar travel time is abstracted (impact resolves at the target on fire).

See `docs/DESIGN.md` for the full design reference and `ATTRIBUTION.md` for asset notes.
