using System;
using System.Collections.Generic;

namespace Tidewatch.Core
{
    /// <summary>Live enemy in the sim. Position is continuous (grid units).</summary>
    public sealed class Enemy
    {
        public int Id;
        public EnemyDef Def;
        public float Hp;
        public float MaxHp;
        // Continuous position in tile space.
        public float X, Y;
        public float SpeedMult = 1f;
        public float SlowTimer;
        public float SlowPct;          // active slow fraction while SlowTimer > 0
        public bool Beached;
        public bool ShroudedActive;    // currently untargetable by direct fire
        public float ArmorShred;       // flat armor removed
        public float SpitTimer;
        public float TidecallTimer;
        public bool Dead;
        public bool ReachedBase;
        // Current waypoint path (grid steps) and progress.
        public List<GridPos> Path = new List<GridPos>();
        public int PathIndex;
        /// <summary>Progress along the whole route for First/Last targeting (higher = further).</summary>
        public float RouteProgress;
    }

    /// <summary>Events the Game layer listens to for visuals/audio. All optional.</summary>
    public sealed class SimEvents
    {
        public Action<Enemy> OnEnemySpawned;
        public Action<Enemy> OnEnemyDied;          // killed (bounty paid)
        public Action<Enemy> OnEnemyLeaked;        // reached base
        public Action<TowerInstance, Enemy> OnTowerFired;
        public Action<GridPos, float> OnAreaIlluminated; // flare impact
        public Action<TowerInstance> OnTowerDisabled;
        public Action<TowerInstance> OnTowerReenabled;
        public Action OnTidecall;
        public Action<int> OnLanternDamaged;
        public Action<int> OnSalvageChanged;
        public Action<TidePhase> OnTideTurn;
        public Action OnWaveCleared;
        public Action OnVictory;
        public Action OnDefeat;
    }

    /// <summary>
    /// The authoritative real-time simulation. Pure C# (no MonoBehaviour, no UnityEngine),
    /// so it is deterministic given a run seed and fully EditMode-testable. The Game layer
    /// feeds it dt and renders its state. All combat/hot-path collections are pooled/reused.
    /// </summary>
    public sealed class GameSim
    {
        public ContentDb Db { get; }
        public TileGrid Grid { get; }
        public TideSystem Tide { get; }
        public PathService Paths { get; }
        public Economy Economy { get; }
        public SimEvents Events { get; } = new SimEvents();
        public SeededRng Rng { get; private set; }

        public DifficultyDef Difficulty { get; }
        public int LanternLight { get; private set; }
        public int LanternLightMax { get; }

        public readonly List<Enemy> Enemies = new List<Enemy>();
        public readonly List<TowerInstance> Towers = new List<TowerInstance>();
        private readonly List<WaveDef> _waves;
        public int WaveCount => _waves.Count;
        public int NextWaveIndex { get; private set; }   // 0-based; == WaveCount => done
        public bool WaveActive { get; private set; }
        public bool Endless { get; private set; }
        public bool GameOver { get; private set; }
        public bool Won { get; private set; }

        // Run stats.
        public int Leaks { get; private set; }
        public int SalvageEarned { get; private set; }
        public int TowersBuilt { get; private set; }
        public float Elapsed { get; private set; }

        // Active wave spawn schedule.
        private List<(float time, string enemyId, int gate)> _spawnSchedule;
        private int _spawnCursor;
        private float _waveClock;
        private float _waveScheduledLength;
        private int _nextEnemyId = 1;

        private readonly string _levelId;
        private readonly ulong _runSeed;

        public GameSim(ContentDb db, TileGrid grid, TideSystem tide, IList<WaveDef> waves,
            DifficultyDef difficulty, string levelId, ulong runSeed, bool endless)
        {
            Db = db;
            Grid = grid;
            Tide = tide;
            Difficulty = difficulty;
            _levelId = levelId;
            _runSeed = runSeed == 0 ? 1UL : runSeed;
            Endless = endless;
            _waves = new List<WaveDef>(waves);
            Paths = new PathService(grid);
            Economy = new Economy(difficulty.StartingSalvage);
            LanternLightMax = difficulty.LanternLight;
            LanternLight = LanternLightMax;
            Rng = new SeededRng(_runSeed);
            NextWaveIndex = 0;
            grid.ApplyTidePhase(tide.CurrentPhase);
            Paths.RecomputeAll();
            Tide.OnPhaseTurn += HandleTideTurn;
        }

        // ------------------------------------------------------------------
        // Building / selling / upgrading
        // ------------------------------------------------------------------

        public bool TryBuildTower(string towerId, GridPos plot, out string failReason)
        {
            failReason = null;
            if (GameOver) { failReason = "Game is over."; return false; }
            if (!Db.TryGetTower(towerId, out var def)) { failReason = "Unknown tower."; return false; }
            var tile = Grid.Get(plot);
            if (tile == null || tile.Terrain != TerrainType.BuildPlot)
            { failReason = "Must build on a raised plot."; return false; }
            if (tile.OccupiedByTowerId != null)
            { failReason = "Plot already occupied."; return false; }
            int cost = def.Tiers[0].Cost;
            if (!Economy.CanAfford(cost))
            { failReason = "Not enough Salvage."; return false; }

            Economy.TrySpend(cost);
            bool adjacentPrism = HasAdjacentPrism(plot);
            var inst = new TowerInstance(def, plot, adjacentPrism);
            Grid.TryPlaceTower(plot, towerId);
            Towers.Add(inst);
            TowersBuilt++;
            Events.OnSalvageChanged?.Invoke(Economy.Salvage);
            return true;
        }

        private bool HasAdjacentPrism(GridPos plot)
        {
            foreach (var n in Grid.Neighbours(plot))
            {
                var t = Grid.Get(n);
                if (t != null && t.OccupiedByTowerId == TowerIds.PrismArray) return true;
            }
            return false;
        }

        public bool TrySellTower(TowerInstance inst, out int refund)
        {
            refund = 0;
            if (inst == null || !Towers.Contains(inst)) return false;
            refund = Economy.SellRefund(inst.TotalInvested);
            Economy.AddSalvage(refund);
            Grid.TryRemoveTower(inst.Plot);
            Towers.Remove(inst);
            Events.OnSalvageChanged?.Invoke(Economy.Salvage);
            return true;
        }

        public bool TryUpgradeTower(TowerInstance inst)
        {
            if (inst == null || GameOver) return false;
            bool ok = inst.TryUpgrade(Economy);
            if (ok) Events.OnSalvageChanged?.Invoke(Economy.Salvage);
            return ok;
        }

        public bool TryPickBranch(TowerInstance inst, bool branchA)
        {
            if (inst == null || GameOver) return false;
            bool ok = inst.TryPickBranch(branchA, Economy);
            if (ok) Events.OnSalvageChanged?.Invoke(Economy.Salvage);
            return ok;
        }

        // ------------------------------------------------------------------
        // Wave control
        // ------------------------------------------------------------------

        /// <summary>Call the next wave. If called while a wave is active, pays early-call bonus.</summary>
        public bool TryCallWave()
        {
            if (GameOver) return false;
            if (WaveActive) return false; // one wave at a time
            if (NextWaveIndex >= WaveCount && !Endless) return false;

            WaveDef wave;
            if (NextWaveIndex < WaveCount)
            {
                wave = _waves[NextWaveIndex];
            }
            else
            {
                // Endless: generate a scaled wave deterministically.
                wave = GenerateEndlessWave(NextWaveIndex);
            }
            StartWave(wave);
            NextWaveIndex++;
            return true;
        }

        /// <summary>Call the wave early; grants a bonus for the time skipped.</summary>
        public int CallWaveEarlyBonus()
        {
            // Bonus is for time remaining on the current wave's schedule.
            float remaining = WaveActive ? _waveScheduledLength - _waveClock : 0f;
            return Economy.EarlyCallBonus(remaining);
        }

        private void StartWave(WaveDef wave)
        {
            WaveActive = true;
            _waveClock = 0f;
            _spawnCursor = 0;
            _spawnSchedule = WaveSystem.BuildSpawnSchedule(wave, Rng);
            _waveScheduledLength = _spawnSchedule.Count > 0 ? _spawnSchedule[_spawnSchedule.Count - 1].time : 0f;
        }

        private WaveDef GenerateEndlessWave(int index)
        {
            // Deterministic scaling from run seed + index.
            int tier = index - WaveCount + 1;
            var wave = new WaveDef { VarianceSeed = 0 };
            int gates = Math.Max(1, Grid.Gates.Count);
            string[] pool = {
                EnemyIds.Skitterling, EnemyIds.BrineHulk, EnemyIds.AbyssalLurker,
                EnemyIds.Spitter, EnemyIds.Broodmother
            };
            int entries = 2 + (tier % 3);
            for (int i = 0; i < entries; i++)
            {
                string id = pool[Rng.Range(0, pool.Length)];
                int count = 6 + tier * 2 + Rng.Range(0, 4);
                wave.Entries.Add(new SpawnEntry(id, count, 0.6f, Rng.Range(0, gates), i * 2f));
            }
            return wave;
        }

        // ------------------------------------------------------------------
        // Main tick
        // ------------------------------------------------------------------

        public void Tick(float dt)
        {
            if (GameOver) return;
            Elapsed += dt;

            // Tide.
            if (Tide.Tick(dt))
            {
                // phase turned; HandleTideTurn already applied via event
            }

            // Spawning.
            if (WaveActive)
            {
                _waveClock += dt;
                while (_spawnCursor < _spawnSchedule.Count && _spawnSchedule[_spawnCursor].time <= _waveClock)
                {
                    var s = _spawnSchedule[_spawnCursor];
                    SpawnEnemy(s.enemyId, s.gate);
                    _spawnCursor++;
                }
            }

            // Enemies.
            for (int i = Enemies.Count - 1; i >= 0; i--)
            {
                var e = Enemies[i];
                if (e.Dead) { Enemies.RemoveAt(i); continue; }
                TickEnemy(e, dt);
                if (e.ReachedBase)
                {
                    Enemies.RemoveAt(i);
                    Leak(e);
                }
            }

            // Towers.
            foreach (var t in Towers)
            {
                if (t.TickDisabled(dt)) Events.OnTowerReenabled?.Invoke(t);
                if (!t.IsDisabled) TickTower(t, dt);
            }

            // Wave clear check.
            if (WaveActive && _spawnCursor >= _spawnSchedule.Count && Enemies.Count == 0)
            {
                WaveActive = false;
                OnWaveCleared();
            }
        }

        private void OnWaveCleared()
        {
            Economy.AddSalvage(Economy.WaveCompletionBonus);
            SalvageEarned += Economy.WaveCompletionBonus;
            int dividend = Economy.PayReserveInterest();
            SalvageEarned += dividend;
            Events.OnSalvageChanged?.Invoke(Economy.Salvage);
            Events.OnWaveCleared?.Invoke();

            if (!Endless && NextWaveIndex >= WaveCount)
            {
                // Final wave cleared. If the lantern is still lit, victory.
                if (LanternLight > 0)
                {
                    Won = true;
                    GameOver = true;
                    Events.OnVictory?.Invoke();
                }
                // If LanternLight == 0 here, defeat already fired (0 takes precedence).
            }
        }

        // ------------------------------------------------------------------
        // Tide
        // ------------------------------------------------------------------

        private void HandleTideTurn(TidePhase phase)
        {
            Grid.ApplyTidePhase(phase);
            Paths.RecomputeAll();
            // Living enemies re-path within this same tick; pelagic enemies caught on a
            // drying tile become Beached; beached enemies on reflooded tiles recover.
            foreach (var e in Enemies) Repath(e);
            Events.OnTideTurn?.Invoke(phase);
        }

        /// <summary>Recompute an enemy's remaining path from its current tile.</summary>
        private void Repath(Enemy e)
        {
            GridPos cur = new GridPos((int)Math.Floor(e.X), (int)Math.Floor(e.Y));
            var field = Paths.For(e.Def.MoveClass);

            var tile = Grid.Get(cur);
            // Pelagic beaching: on a dry tile with no water.
            if (e.Def.MoveClass == MoveClass.Pelagic && tile != null && !tile.IsWater &&
                tile.Terrain != TerrainType.Gate && tile.Terrain != TerrainType.Base)
            {
                e.Beached = true;
            }
            else if (e.Beached && tile != null && tile.IsWater)
            {
                e.Beached = false;
            }

            if (!field.IsReachable(cur))
            {
                // Surrounded / no valid path: keep current path if still usable, else the
                // enemy slows (Beached-equivalent) but never teleports or soft-locks.
                if (e.Def.MoveClass == MoveClass.Terrestrial) e.SlowTimer = Math.Max(e.SlowTimer, 0.5f);
                return;
            }
            var path = field.BuildPath(cur);
            if (path.Count > 0)
            {
                e.Path = path;
                e.PathIndex = 0;
            }
        }

        // ------------------------------------------------------------------
        // Enemies
        // ------------------------------------------------------------------

        private void SpawnEnemy(string enemyId, int gateIndex)
        {
            if (!Db.TryGetEnemy(enemyId, out var def)) return;
            if (Grid.Gates.Count == 0) return;
            var gate = Grid.Gates[Math.Clamp(gateIndex, 0, Grid.Gates.Count - 1)];
            var e = new Enemy
            {
                Id = _nextEnemyId++,
                Def = def,
                MaxHp = def.BaseHp * Difficulty.EnemyHpMult,
                Hp = def.BaseHp * Difficulty.EnemyHpMult,
                X = gate.X + 0.5f,
                Y = gate.Y + 0.5f,
                SpitTimer = def.SpitInterval,
                TidecallTimer = def.TidecallInterval,
                ShroudedActive = def.Shrouded,
            };
            Repath(e);
            Enemies.Add(e);
            Events.OnEnemySpawned?.Invoke(e);
        }

        private void TickEnemy(Enemy e, float dt)
        {
            // Slow decay.
            float speed = e.Def.BaseSpeed * Difficulty.EnemySpeedMult * e.SpeedMult;
            if (e.SlowTimer > 0f)
            {
                e.SlowTimer -= dt;
                speed *= (1f - e.SlowPct);
            }
            if (e.Beached) speed *= 0.4f;

            // Boss Tidecall.
            if (e.Def.IsBoss && e.Def.TidecallInterval > 0f)
            {
                e.TidecallTimer -= dt;
                if (e.TidecallTimer <= 0f)
                {
                    e.TidecallTimer = e.Def.TidecallInterval;
                    Tide.ForceSurge();
                    Events.OnTidecall?.Invoke();
                }
            }

            // Spitter attack.
            if (e.Def.SpitInterval > 0f)
            {
                e.SpitTimer -= dt;
                if (e.SpitTimer <= 0f)
                {
                    e.SpitTimer = e.Def.SpitInterval;
                    SpitAtNearestTower(e);
                }
            }

            // Move along path.
            MoveAlongPath(e, speed * dt);

            // Shroud state recomputed against illumination each tick.
            UpdateShroud(e);
        }

        private void MoveAlongPath(Enemy e, float dist)
        {
            float remaining = dist;
            int guard = 64;
            while (remaining > 0f && guard-- > 0)
            {
                if (e.PathIndex >= e.Path.Count)
                {
                    // Reached the end of the path (base).
                    e.ReachedBase = true;
                    return;
                }
                var node = e.Path[e.PathIndex];
                float tx = node.X + 0.5f, ty = node.Y + 0.5f;
                float dx = tx - e.X, dy = ty - e.Y;
                float d = (float)Math.Sqrt(dx * dx + dy * dy);
                if (d <= remaining)
                {
                    e.X = tx; e.Y = ty;
                    remaining -= d;
                    e.PathIndex++;
                    e.RouteProgress += d;
                }
                else
                {
                    e.X += dx / d * remaining;
                    e.Y += dy / d * remaining;
                    e.RouteProgress += remaining;
                    remaining = 0f;
                }
            }
        }

        private void UpdateShroud(Enemy e)
        {
            if (!e.Def.Shrouded) { e.ShroudedActive = false; return; }
            e.ShroudedActive = !IsIlluminated(e.X, e.Y);
        }

        /// <summary>Is a point illuminated by any light tower or the Lantern aura?</summary>
        public bool IsIlluminated(float x, float y)
        {
            // Lantern aura at base.
            var bp = Grid.BasePos;
            float bx = bp.X + 0.5f, by = bp.Y + 0.5f;
            float dx = x - bx, dy = y - by;
            const float lanternAura = 3.5f;
            if (dx * dx + dy * dy <= lanternAura * lanternAura) return true;

            foreach (var t in Towers)
            {
                if (t.IsDisabled) continue;
                var def = Db.GetTower(t.DefId);
                if (!def.EmitsLight) continue;
                var s = t.ResolveStats();
                if (s.IlluminationRadius <= 0f) continue;
                float tx = t.Plot.X + 0.5f, ty = t.Plot.Y + 0.5f;
                float ddx = x - tx, ddy = y - ty;
                if (ddx * ddx + ddy * ddy <= s.IlluminationRadius * s.IlluminationRadius)
                    return true;
            }
            return false;
        }

        private void SpitAtNearestTower(Enemy e)
        {
            TowerInstance best = null;
            float bestD = float.MaxValue;
            foreach (var t in Towers)
            {
                if (t.IsDisabled) continue;
                float d = GridPos.SqrDistance(new GridPos((int)e.X, (int)e.Y), t.Plot);
                if (d < bestD) { bestD = d; best = t; }
            }
            if (best != null && bestD <= 6f * 6f)
            {
                best.DisabledTimer = e.Def.SpitDisableDuration;
                best.CurrentTargetId = -1;
                Events.OnTowerDisabled?.Invoke(best);
            }
        }

        private void Leak(Enemy e)
        {
            int dmg = Math.Max(1, (int)(e.Def.LeakDamage * Difficulty.LeakMult));
            LanternLight -= dmg;
            Leaks++;
            Events.OnEnemyLeaked?.Invoke(e);
            Events.OnLanternDamaged?.Invoke(LanternLight);
            // Documented rule: defeat at 0 takes precedence over a simultaneous final kill.
            if (LanternLight <= 0)
            {
                LanternLight = 0;
                GameOver = true;
                Won = false;
                Events.OnDefeat?.Invoke();
            }
        }

        /// <summary>Apply damage to an enemy; handles armor, beached bonus, split-on-death.</summary>
        public void DamageEnemy(Enemy e, float rawDamage, TowerInstance source, bool isFlare)
        {
            if (e.Dead || GameOver) return;
            float armor = Math.Max(0f, e.Def.Armor - e.ArmorShred);
            float dmg = Math.Max(1f, rawDamage - armor);
            if (isFlare && e.Beached && source != null)
            {
                var def = Db.GetTower(source.DefId);
                dmg *= def.BonusVsBeached;
            }
            e.Hp -= dmg;
            if (e.Hp <= 0f) Kill(e, source);
        }

        private void Kill(Enemy e, TowerInstance source)
        {
            if (e.Dead) return;
            e.Dead = true;
            int bounty = Economy.KillBounty(e.Def, Difficulty.BountyMult);
            Economy.AddSalvage(bounty);
            SalvageEarned += bounty;
            Events.OnSalvageChanged?.Invoke(Economy.Salvage);
            Events.OnEnemyDied?.Invoke(e);

            // Broodmother splits into Skitterlings.
            if (!string.IsNullOrEmpty(e.Def.SplitIntoId) && Db.TryGetEnemy(e.Def.SplitIntoId, out var child))
            {
                for (int i = 0; i < e.Def.SplitCount; i++)
                {
                    var c = new Enemy
                    {
                        Id = _nextEnemyId++,
                        Def = child,
                        MaxHp = child.BaseHp * Difficulty.EnemyHpMult,
                        Hp = child.BaseHp * Difficulty.EnemyHpMult,
                        X = e.X + Rng.Range(-0.3f, 0.3f),
                        Y = e.Y + Rng.Range(-0.3f, 0.3f),
                    };
                    Repath(c);
                    Enemies.Add(c);
                    Events.OnEnemySpawned?.Invoke(c);
                }
            }
        }

        // ------------------------------------------------------------------
        // Towers / combat
        // ------------------------------------------------------------------

        private void TickTower(TowerInstance t, float dt)
        {
            var def = Db.GetTower(t.DefId);
            if (!def.DealsDamage) { TickFogBell(t, def, dt); return; }

            // Acquire a target.
            Enemy target = AcquireTarget(t, def);
            if (target == null)
            {
                t.CurrentTargetId = -1;
                t.RampTime = 0f;
                return;
            }

            // Beacon ramp: RampTime accumulates every tick the beam holds the same target,
            // and each discrete shot's damage is scaled by it (see Fire). This models a
            // continuous ramping beam while reusing the standard fire-rate gate.
            if (def.Id == TowerIds.BeaconSpire)
            {
                if (t.CurrentTargetId == target.Id) t.RampTime += dt;
                else { t.CurrentTargetId = target.Id; t.RampTime = 0f; }
            }

            // Fire rate gate: only discharge when the cooldown elapses.
            _fireCooldown.TryGetValue(t, out float cd);
            cd -= dt;
            if (cd > 0f) { _fireCooldown[t] = cd; return; }
            var stats = t.ResolveStats();
            cd = stats.FireRate > 0f ? 1f / stats.FireRate : 0.5f;
            _fireCooldown[t] = cd;

            Fire(t, def, stats, target);
        }

        private readonly Dictionary<TowerInstance, float> _fireCooldown = new Dictionary<TowerInstance, float>();

        private void Fire(TowerInstance t, TowerDef def, TowerTierStats stats, Enemy target)
        {
            Events.OnTowerFired?.Invoke(t, target);
            switch (def.Id)
            {
                case TowerIds.BeaconSpire:
                {
                    float rampMult = 1f + Math.Min(2f, t.RampTime * 0.5f); // up to 3x ramp
                    float dmg = stats.Damage * rampMult;
                    var branch = t.ActiveBranch();
                    if (branch != null && branch.BurstWindow && t.RampTime > 3f) dmg *= 1.5f; // Solar Lance
                    DamageEnemy(target, dmg, t, false);
                    if (branch != null && branch.AppliesSlowOnHit) // Dusk Beam
                    {
                        target.SlowPct = 0.3f;
                        target.SlowTimer = Math.Max(target.SlowTimer, 0.8f);
                    }
                    break;
                }
                case TowerIds.FlareMortar:
                {
                    // Area damage around target with travel time abstracted; illuminates impact.
                    float r = 1.5f;
                    foreach (var other in EnemiesWithin(target.X, target.Y, r))
                        DamageEnemy(other, stats.Damage, t, true);
                    Events.OnAreaIlluminated?.Invoke(
                        new GridPos((int)target.X, (int)target.Y), 1.5f);
                    break;
                }
                case TowerIds.PrismArray:
                {
                    // Chain-light arcs to N nearest additional enemies.
                    var chain = new List<Enemy> { target };
                    Enemy cur = target;
                    for (int arc = 0; arc < stats.ChainArcs; arc++)
                    {
                        Enemy next = NearestEnemy(cur.X, cur.Y, 3f, chain);
                        if (next == null) break;
                        chain.Add(next);
                        cur = next;
                    }
                    float dmg = stats.Damage;
                    foreach (var c in chain)
                    {
                        DamageEnemy(c, dmg, t, false);
                        dmg *= 0.85f; // falloff per arc
                    }
                    break;
                }
                case TowerIds.HarpoonBallista:
                {
                    // Pierces in a line toward the target.
                    var dir = (target.X - (t.Plot.X + 0.5f), target.Y - (t.Plot.Y + 0.5f));
                    float len = (float)Math.Sqrt(dir.Item1 * dir.Item1 + dir.Item2 * dir.Item2);
                    if (len < 1e-4f) { DamageEnemy(target, stats.Damage, t, false); break; }
                    float nx = dir.Item1 / len, ny = dir.Item2 / len;
                    int hits = 0;
                    foreach (var e in EnemiesAlongLine(t.Plot.X + 0.5f, t.Plot.Y + 0.5f, nx, ny, stats.Range))
                    {
                        DamageEnemy(e, stats.Damage, t, false);
                        if (++hits > stats.Pierce) break;
                    }
                    break;
                }
            }
        }

        private void TickFogBell(TowerInstance t, TowerDef def, float dt)
        {
            _fireCooldown.TryGetValue(t, out float cd);
            cd -= dt;
            if (cd > 0f) { _fireCooldown[t] = cd; return; }
            var stats = t.ResolveStats();
            cd = stats.FireRate > 0f ? 1f / stats.FireRate : 1f;
            _fireCooldown[t] = cd;

            // Pulse: slow + armor shred everything in radius. Reveal is passive via EmitsLight.
            foreach (var e in EnemiesWithin(t.Plot.X + 0.5f, t.Plot.Y + 0.5f, stats.Range))
            {
                e.SlowPct = Math.Max(e.SlowPct, stats.SlowPct);
                e.SlowTimer = Math.Max(e.SlowTimer, 1.0f);
                if (stats.ArmorShred > 0f) e.ArmorShred = Math.Max(e.ArmorShred, stats.ArmorShred);
            }
            Events.OnTowerFired?.Invoke(t, null);
        }

        /// <summary>Targeting with selectable priority; applies the Shroud rule.</summary>
        private Enemy AcquireTarget(TowerInstance t, TowerDef def)
        {
            var stats = t.ResolveStats();
            float rangeSqr = stats.Range * stats.Range;
            float tx = t.Plot.X + 0.5f, ty = t.Plot.Y + 0.5f;

            Enemy best = null;
            float bestScore = 0f;
            foreach (var e in Enemies)
            {
                if (e.Dead || e.ReachedBase) continue;
                float dx = e.X - tx, dy = e.Y - ty;
                if (dx * dx + dy * dy > rangeSqr) continue;
                // Shroud: direct-fire towers cannot target Shrouded enemies.
                if (def.DirectFire && e.ShroudedActive) continue;

                float score;
                switch (t.Priority)
                {
                    case TargetPriority.Last: score = -e.RouteProgress; break;
                    case TargetPriority.Strongest: score = e.Hp; break;
                    case TargetPriority.Closest: score = -(dx * dx + dy * dy); break;
                    case TargetPriority.First:
                    default: score = e.RouteProgress; break;
                }
                if (best == null || score > bestScore)
                {
                    best = e;
                    bestScore = score;
                }
            }
            return best;
        }

        // Non-allocating-ish helpers that reuse buffers (hot path: no LINQ, pooled lists).
        private readonly List<Enemy> _buffer = new List<Enemy>(256);

        private List<Enemy> EnemiesWithin(float x, float y, float r)
        {
            _buffer.Clear();
            float rs = r * r;
            foreach (var e in Enemies)
            {
                if (e.Dead || e.ReachedBase) continue;
                float dx = e.X - x, dy = e.Y - y;
                if (dx * dx + dy * dy <= rs) _buffer.Add(e);
            }
            return _buffer;
        }

        private Enemy NearestEnemy(float x, float y, float r, List<Enemy> exclude)
        {
            float rs = r * r;
            Enemy best = null;
            float bestD = float.MaxValue;
            foreach (var e in Enemies)
            {
                if (e.Dead || e.ReachedBase || exclude.Contains(e)) continue;
                float dx = e.X - x, dy = e.Y - y;
                float d = dx * dx + dy * dy;
                if (d <= rs && d < bestD) { bestD = d; best = e; }
            }
            return best;
        }

        private List<Enemy> EnemiesAlongLine(float x, float y, float nx, float ny, float len)
        {
            _buffer.Clear();
            foreach (var e in Enemies)
            {
                if (e.Dead || e.ReachedBase) continue;
                float rx = e.X - x, ry = e.Y - y;
                float along = rx * nx + ry * ny;
                if (along < 0f || along > len) continue;
                float perp = Math.Abs(rx * ny - ry * nx);
                if (perp <= 0.6f) _buffer.Add(e);
            }
            _buffer.Sort((a, b) =>
            {
                float da = (a.X - x) * nx + (a.Y - y) * ny;
                float dbb = (b.X - x) * nx + (b.Y - y) * ny;
                return da.CompareTo(dbb);
            });
            return _buffer;
        }

        // ------------------------------------------------------------------
        // Save / load
        // ------------------------------------------------------------------

        public RunSave ToSave()
        {
            var (s0, s1) = Rng.GetState();
            var save = new RunSave
            {
                runSeed = _runSeed,
                rngS0 = s0,
                rngS1 = s1,
                levelId = _levelId,
                difficultyId = Difficulty.Id,
                waveIndex = NextWaveIndex,
                tideIndex = Tide.CurrentIndex,
                tideClock = Tide.PhaseClock,
                salvage = Economy.Salvage,
                lanternLight = LanternLight,
                endless = Endless,
                leaks = Leaks,
                salvageEarned = SalvageEarned,
                towersBuilt = TowersBuilt,
                elapsed = Elapsed,
            };
            foreach (var t in Towers)
            {
                save.towers.Add(new TowerSave
                {
                    defId = t.DefId,
                    x = t.Plot.X,
                    y = t.Plot.Y,
                    tier = t.Tier,
                    branchId = t.BranchId,
                    priority = (int)t.Priority,
                    totalInvested = t.TotalInvested,
                    disabledTimer = t.DisabledTimer,
                });
            }
            return save;
        }

        /// <summary>Restore a sim from a wave-boundary save (no live enemies — saved at wave clear).</summary>
        public static GameSim FromSave(RunSave save, ContentDb db, TileGrid grid, TideSystem tide,
            IList<WaveDef> waves, DifficultyDef difficulty)
        {
            var sim = new GameSim(db, grid, tide, waves, difficulty, save.levelId, save.runSeed, save.endless);
            sim.Rng = SeededRng.FromState(save.rngS0, save.rngS1);
            sim.NextWaveIndex = save.waveIndex;
            sim.Tide.SetState(save.tideIndex, save.tideClock);
            sim.Grid.ApplyTidePhase(sim.Tide.CurrentPhase);
            sim.Paths.RecomputeAll();
            sim.Economy.SetSalvage(save.salvage);
            sim.LanternLight = save.lanternLight;
            sim.Leaks = save.leaks;
            sim.SalvageEarned = save.salvageEarned;
            sim.TowersBuilt = save.towersBuilt;
            sim.Elapsed = save.elapsed;
            foreach (var ts in save.towers)
            {
                if (!db.TryGetTower(ts.defId, out var def)) continue;
                var plot = new GridPos(ts.x, ts.y);
                bool adjacentPrism = sim.HasAdjacentPrism(plot);
                var inst = new TowerInstance(def, plot, adjacentPrism)
                {
                    Tier = ts.tier,
                    BranchId = ts.branchId,
                    Priority = (TargetPriority)ts.priority,
                    TotalInvested = ts.totalInvested,
                    DisabledTimer = ts.disabledTimer,
                };
                grid.TryPlaceTower(plot, ts.defId);
                sim.Towers.Add(inst);
            }
            return sim;
        }
    }
}
