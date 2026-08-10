# PLATFORM PROMPT — Tidewatch: Lantern of the Shattered Coast

## 1. Project Request / Product Identity

Build **Tidewatch: Lantern of the Shattered Coast**, a single-player tower defense game in **Unity (2022.3 LTS or newer) with C#**. The player is the Keeper of the last tidal lighthouse-city on a drowned coastline. Each night, abyssal creatures surge inland with the tide to extinguish the Great Lantern. The Keeper builds **lantern-tech and harpoon towers** on raised plots along the causeways, holds the line through a sequence of waves, and keeps the Lantern lit until dawn.

**Signature twist (must ship): the Tide System.** Every level sits on a tidal flat. A visible Tide Meter cycles through phases (Low → Rising → High → Ebbing) on a per-level schedule. Tile state changes with the tide: dry causeway tiles flood at high tide, and submerged trenches drain at low tide. Enemy movement classes interact with tile state differently (terrestrial, amphibious, pelagic), so **the enemy path graph changes mid-run** and living enemies must re-path when the tide turns. Pelagic enemies caught on a drying tile become **Beached** — slowed and taking bonus damage. A second intertwined mechanic: deep-water **Lurkers are Shrouded** and cannot be targeted by direct-fire towers unless illuminated by a light-source tower or the Lantern's aura.

**Session model:** Level-based campaign. Each level is a fixed sequence of waves (12–20); victory when the final wave is cleared with the Lantern still lit; defeat when Lantern Light (base HP) reaches zero. Clearing a level unlocks the next, plus an optional **Endless Night** mode per cleared level.

**Tone:** moody coastal fantasy — fog, brine, whale-song, brass-and-glass lighthouse machinery. Cohesive simple art (low-poly 3D diorama or clean 2D sprites) is expected and acceptable; mismatched asset-pack collage is not.

## 2. Target Users & Primary Jobs-to-be-Done

- **Strategy TD players (primary):** want meaningful build decisions — tower synergies, economy tension, and path manipulation — not idle stat-checks. JTBD: "Let me solve each level like a puzzle with multiple viable solutions."
- **Returning/short-session players:** want to resume a run later and chase better clears. JTBD: "Save my run, remember my records, let me retry fast."
- **Tinkerers/configurators:** want to tune difficulty and inspect content as data. JTBD: "Let me change waves/levels/difficulty without touching code."

## 3. Core Requirements / Entities

### Towers (minimum 5, each with unique behavior — not reskins)
1. **Beacon Spire** — continuous light beam, single target; damage ramps the longer it holds the same target; emits an illumination radius that reveals Shrouded enemies.
2. **Flare Mortar** — lobbed area-damage shells with travel time (can lead moving targets); briefly illuminates the impact zone; bonus damage vs Beached enemies.
3. **Prism Array** — fires chain-light that arcs between up to N nearby enemies; gains +1 arc when built adjacent to another Prism ("resonance").
4. **Harpoon Ballista** — fast physical bolt, pierces in a line; cheap and reliable; cannot hit Shrouded targets.
5. **Fog Bell** — support tower, no damage; pulses slow all enemies in radius; upgrades can add armor-shred or reveal.

**Upgrades:** each tower has 3 tiers; tiers 1–2 are linear stat/behavior improvements, tier 3 is a **branch choice between two mutually exclusive capstones** (e.g., Beacon Spire → *Solar Lance*: burst damage window, vs *Dusk Beam*: beam also slows). All tower stats, costs, and upgrade effects must live in data assets (ScriptableObjects or JSON), not hardcoded in behavior scripts.

### Enemies (minimum 5 classes + 1 boss)
- **Skitterling Shoal** — fast, fragile, spawned in packs.
- **Brine Hulk** — slow, armored (flat damage reduction), terrestrial.
- **Abyssal Lurker** — pelagic; Shrouded unless illuminated; travels water tiles.
- **Spitter** — terrestrial; periodically spits at a tower, disabling it for a few seconds (disabled towers show a clear visual state).
- **Broodmother** — amphibious mini-boss; splits into Skitterlings on death.
- **The Drowned Bell (boss, final wave of campaign levels designated boss-levels)** — massive HP pool; periodically sounds a **Tidecall** that forces an immediate tide surge; escorts spawn with it.

Each enemy has: HP, speed, armor, salvage bounty, leak damage (Lantern Light lost if it reaches the base), movement class, and optional traits (Shrouded, spitter attack, split-on-death).

### Base & resources
- **The Great Lantern** (base): Lantern Light HP; small built-in illumination aura.
- **Salvage** (currency): earned from kills and wave-completion bonuses; spent on towers/upgrades; towers sellable at a defined refund rate (e.g., 70%).
- **Keeper's Reserve:** at each wave clear, the player earns a small interest dividend (e.g., +4%, capped) on unspent Salvage — an explicit thrift-vs-spend tension that must be documented in the design notes.

## 4. Major Feature Areas

- **Core loop:** real-time simulation at 60 fps target — select plot → build/upgrade → enemies spawn per wave schedule → pathfind over current tide state → towers acquire targets (selectable priority: First / Last / Strongest / Closest) → combat resolves → salvage accrues → next wave (auto or player-called early for a bonus). Pause, 1×, and 2× speed controls required.
- **Tide System:** per-level tide schedule (phase durations per wave or continuous timer); tile flood/drain transitions are animated and recompute pathability; mid-path enemies re-path within one simulation tick; Beached state applied/cleared on transitions.
- **Pathfinding:** grid-based A* or BFS per movement class over the current tile-state graph; enemies may not walk through blocked/build plots; multiple spawn gates and multiple lanes must be supported by the level format.
- **Wave system:** data-driven wave compositions (enemy type, count, spawn interval, gate, spawn delay); seeded RNG for any composition variance so runs are reproducible from a run seed.
- **Economy:** kill bounties, wave bonus, early-call bonus, Reserve interest, sell refunds; all values configurable per difficulty.
- **Save/Load:** full mid-run save at wave boundaries (acceptable simplification — must be stated in README): towers with tiers/targeting, Salvage, Lantern Light, wave index, tide phase, difficulty, run seed. At least 3 save slots. Plus persistent meta data: unlocked levels, best wave reached per level per difficulty, settings.
- **Difficulty:** three presets — **Calm Sea / Rising Gale / Abyssal Night** — modifying enemy HP/speed, bounty multipliers, starting Salvage, Lantern Light, and tide cadence. Difficulty selectable per level; records tracked per difficulty.
- **Configurable levels:** minimum **4 campaign levels** shipped, each defined entirely as data (tile grid incl. elevations/water depth, build plots, gates, base position, tide schedule, wave list, par time). Adding a new level must require **zero C# changes**.
- **Audio:** SFX for each tower's fire, enemy deaths, tower disable, wave-start horn, tide-turn surge sting, Lantern damage, UI interactions, plus looping ocean ambience and one music bed. Audio mixer groups (Master/Music/SFX) with volume sliders and mute.
- **Game feel ("juice-light"):** muzzle/beam flashes, hit flashes, death pop + salvage pickup fly-to-HUD, screen shake toggle, tide water rising animation, damage numbers optional (toggleable).

## 5. Domain-Specific Workflows

**Happy path (a run):** Main menu → Level Select (shows unlock state + best clear per difficulty) → difficulty chosen → pre-game briefing panel (map preview, tide schedule hint, enemy classes expected) → build phase with starting Salvage → call first wave → mid-run: build/upgrade/sell, call waves early, watch tide meter and reposition strategy at tide turns → final wave/boss → Victory screen (stats: leaks, salvage earned, towers built, time; records updated) → next level unlocked.

**Edge cases that must be handled gracefully:**
- Placement rejected (insufficient Salvage, non-plot tile, occupied plot): clear red tint + reason hint; no silent failures.
- Tide turns while enemies are mid-path: re-path, never teleport, never soft-lock; if a terrestrial enemy is somehow surrounded by water it takes the shortest valid path or becomes Beached-equivalent (slowed), never stuck.
- Pelagic enemy's tile dries: Beached state applied with visual + Flare Mortar bonus applies.
- Shrouded enemy leaves illumination: towers drop it as a target mid-volley without errors.
- Spitter disables the only tower covering a lane: disable must expire reliably even while paused/unpaused and across save/load.
- Player sells a tower while its projectiles are in flight: in-flight projectiles resolve harmlessly; no null references.
- Save file corrupted or from an older version: detect, report, and fall back to a fresh run without crashing; save format must carry a version number.
- Lantern Light reaches exactly 0 on the same tick the last enemy dies: defeat takes precedence (documented rule).
- 2× speed + Endless mode late waves (100+ live enemies): must hold interactive framerate on modest hardware.

## 6. Data & Persistence

- **Local persistence only** (no backend): JSON or binary save files in `Application.persistentDataPath`; settings in a separate file; records/unlocks in a third. Atomic writes (temp file + rename) to avoid corrupt saves.
- **Content as data:** tower defs, enemy defs, upgrade branches, wave lists, level layouts, difficulty presets all as ScriptableObjects (or JSON with a documented schema). Balance changes must be possible without code edits.
- **Save contents:** run seed, level id, difficulty id, wave index, tide phase + phase clock, Salvage, Lantern Light, full tower list (plot, type, tier, branch, targeting mode, disabled timer), records-relevant stats.
- **Settings persisted:** volumes/mute, screen shake, damage numbers, speed preference, quality level.

## 7. UX / Interface Expectations

- **HUD:** Salvage (with Reserve interest preview), Lantern Light, wave X/N with next-wave composition preview icons, Tide Meter with phase label and time-to-turn, speed controls, menu access. All legible at 1080p and 4K (scaled UI).
- **Placement UX:** ghost preview with range ring, validity tint (green/red), illumination-radius preview for light towers, one-click/one-tap build, Esc/right-click cancel, tower inspector panel on select (stats, targeting mode, upgrade buttons with costs and effect deltas, sell with refund shown).
- **Feedback:** floating salvage pickups, disabled-tower icon + countdown, Beached/Shrouded status icons on enemies, boss health bar, tide-turn warning banner 5 seconds ahead.
- **Screens:** main menu, level select, settings, briefing, pause, victory, defeat (with wave reached + retry), Endless-mode results.
- **Accessibility:** pause anytime including during placement, speed control, colorblind-safe validity tints (shape + color, not color alone), remappable or documented hotkeys (1–5 tower select, Space call wave, Esc cancel/pause).
- No placeholder UI: no default Unity gray panels with unstyled text shipped as final screens.

## 8. Quality, Security & Reliability Expectations

- Deterministic core simulation given a run seed (wave variance, crit/ramp rolls if any); seeded RNG injected, no bare `UnityEngine.Random` in gameplay logic.
- Target 60 fps at 1080p with 150 live enemies and 40 towers; no per-frame allocations in the combat hot path (pool projectiles/enemies or justify otherwise in design notes).
- Save versioning + corruption fallback (see §5). No external network calls, telemetry, or account systems.
- Clean separation: pure C# simulation/rules layer (economy, pathfinding, wave parsing, upgrade math, tide state machine) independent of MonoBehaviour rendering so it is unit-testable in EditMode.
- No secrets, no licensed/copyrighted assets; all audio/art either original, primitive, or permissively licensed with an ATTRIBUTION file.

## 9. Documentation & Testing Expectations

- **README:** premise, controls/hotkeys, win/lose rules, how to open in Unity (version), how to run/build, how to add a new level/tower/enemy via data files, known limitations.
- **DESIGN.md (or docs/):** tide state machine diagram/description, movement-class rules table, economy math incl. Reserve interest, upgrade branch rationale, boss behavior, difficulty multipliers table, save schema + versioning policy.
- **Automated tests (Unity Test Framework, EditMode required; PlayMode optional):** pathfinding over a fixture grid including a tide-flip re-path; wave-list parsing/validation (reject bad enemy ids, zero counts); economy (bounty, interest cap, sell refund); upgrade stat/branch application; tide schedule progression and Beached transitions; save serialization round-trip. Logic tests must not depend on scene loading or timing.

## 10. Constraints & Non-Goals

- Single-player, offline. **No** multiplayer/netcode, no accounts, no IAP/ads, no external services.
- Not an asset-showcase project: primitives/low-poly/simple sprites are fine and preferred over incoherent store packs.
- No mid-wave full-state serialization required (wave-boundary saves are the sanctioned simplification).
- Do not fork into a different genre (no hero-unit MOBA hybrid, no roguelike deckbuilder layer) — depth comes from the Tide + Shroud systems.
- Unity + C# is fixed; do not substitute another engine or language for gameplay code.

## 11. Acceptance Criteria

- [ ] Launches from a main menu into a playable level with a build phase and wave start.
- [ ] ≥5 tower types with distinct behaviors, 3 tiers each, tier-3 branch choices, and per-tower targeting priorities.
- [ ] ≥5 enemy classes + the Drowned Bell boss, each obeying documented movement-class rules.
- [ ] Tide Meter visibly cycles; tiles flood/drain; live enemies re-path on tide turns; Beached and Shrouded mechanics demonstrably work.
- [ ] Data-driven waves and ≥4 campaign levels; a new level can be added with no C# changes.
- [ ] Salvage economy with bounties, wave/early-call bonuses, Reserve interest, upgrades, and sell refunds.
- [ ] Victory and defeat flows with stats, restart, and level unlocks; Endless Night unlocks per cleared level.
- [ ] 3 difficulty presets with measurably different parameters and per-difficulty records.
- [ ] Save/load at wave boundaries across 3 slots restores towers, resources, tide phase, and wave index; corrupted saves handled without crash.
- [ ] SFX for all core actions + ambience/music with working mixer sliders and mute.
- [ ] Pause / 1× / 2× controls; placement UX with range/illumination preview and invalid-placement feedback.
- [ ] EditMode test suite covers pathfinding, waves, economy, upgrades, tide transitions, and save round-trip; all pass.
- [ ] README + design docs enable a first play session and content extension without reading source.

## 12. Uniqueness / Anti-Clone Constraints for This Run

- This is **not** a generic medieval orc-and-arrow tower defense. Do not ship goblins/orcs, generic "cannon/archer/mage" tower trios, or a straight-line single lane. The **tidal terrain that rewrites the path graph mid-run** and the **Shroud/illumination targeting rule** are the product's identity; removing either fails the brief.
- Domain terminology must be consistent and coastal-lantern-flavored (Salvage, Lantern Light, Tide Meter, Beached, Shrouded, Keeper's Reserve) — not gold/mana/HP generic labels reskinned.
- Anti-pattern rejects: towers differing only in damage/range numbers; "AI" that is random target picking labeled as strategy; waves that are linear stat scaling with no composition design; placeholder/default Unity UI; a save system that only stores high scores while claiming "save/load."
- Every shipped level must present a distinct tactical problem (e.g., one split-gate level where the tide opens a shortcut, one pelagic-heavy level forcing illumination investment) — not the same layout with bigger numbers.