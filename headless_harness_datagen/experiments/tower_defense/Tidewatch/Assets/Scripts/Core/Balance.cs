using System.Collections.Generic;

namespace Tidewatch.Core
{
    /// <summary>Resolved stats for one tower tier (1-indexed tier in data, 0-indexed here).</summary>
    public sealed class TowerTierStats
    {
        public float Damage;
        public float Range;
        /// <summary>Shots per second (for the Fog Bell: pulses per second).</summary>
        public float FireRate;
        /// <summary>Illumination radius; 0 for non-light towers.</summary>
        public float IlluminationRadius;
        /// <summary>Slow fraction applied (0..0.9). Only support towers.</summary>
        public float SlowPct;
        /// <summary>Armor shred (flat) applied by Fog Bell upgrades.</summary>
        public float ArmorShred;
        /// <summary>Prism chain arc count.</summary>
        public int ChainArcs;
        /// <summary>Harpoon pierce count.</summary>
        public int Pierce;
        /// <summary>Cost to build (tier 0) or upgrade to this tier.</summary>
        public int Cost;
    }

    /// <summary>Full definition of a tower archetype: 3 tiers + tier-3 branches.</summary>
    public sealed class TowerDef
    {
        public string Id;
        public string DisplayName;
        public string Description;
        /// <summary>Base tier stats, length 3 (tier 1, 2, 3).</summary>
        public TowerTierStats[] Tiers;
        /// <summary>Tier-3 branch A. Null fields mean "no change from tier 3 base".</summary>
        public BranchDef BranchA;
        /// <summary>Tier-3 branch B.</summary>
        public BranchDef BranchB;
        /// <summary>Whether this tower's illumination reveals Shrouded enemies.</summary>
        public bool EmitsLight;
        /// <summary>Whether this tower deals damage (false for Fog Bell).</summary>
        public bool DealsDamage;
        /// <summary>Whether this tower is a direct-fire tower blocked by Shroud.</summary>
        public bool DirectFire;
        /// <summary>Bonus damage multiplier vs Beached enemies (1 = none). Flare Mortar.</summary>
        public float BonusVsBeached;
    }

    /// <summary>A tier-3 branch: stat deltas applied on top of tier-3 base.</summary>
    public sealed class BranchDef
    {
        public string Id;
        public string DisplayName;
        public string Description;
        public float DamageMult = 1f;
        public float RangeMult = 1f;
        public float FireRateMult = 1f;
        public float IlluminationMult = 1f;
        public float SlowPctDelta = 0f;
        public float ArmorShredDelta = 0f;
        public int ChainArcsDelta = 0;
        public int PierceDelta = 0;
        /// <summary>Special: adds a slow on hit (Dusk Beam).</summary>
        public bool AppliesSlowOnHit;
        /// <summary>Special: burst window damage window (Solar Lance).</summary>
        public bool BurstWindow;
        public int Cost;
    }

    public sealed class EnemyDef
    {
        public string Id;
        public string DisplayName;
        public float BaseHp;
        /// <summary>Tiles per second.</summary>
        public float BaseSpeed;
        /// <summary>Flat damage reduction per hit.</summary>
        public float Armor;
        public int Bounty;
        /// <summary>Lantern Light lost if this reaches the base.</summary>
        public int LeakDamage;
        public MoveClass MoveClass;
        public bool Shrouded;
        /// <summary>Spitter: seconds between spits; tower disabled this long.</summary>
        public float SpitInterval;
        public float SpitDisableDuration;
        /// <summary>Broodmother: enemy id to split into on death, count.</summary>
        public string SplitIntoId;
        public int SplitCount;
        /// <summary>Drowned Bell: seconds between forced Tidecall surges.</summary>
        public float TidecallInterval;
        public bool IsBoss;
    }

    public sealed class DifficultyDef
    {
        public string Id;
        public string DisplayName;
        public float EnemyHpMult = 1f;
        public float EnemySpeedMult = 1f;
        public float BountyMult = 1f;
        public int StartingSalvage = 200;
        public int LanternLight = 20;
        /// <summary>Multiplies tide phase durations (>1 = slower tide, <1 = faster).</summary>
        public float TideCadenceMult = 1f;
        /// <summary>Multiplier on leak damage.</summary>
        public float LeakMult = 1f;
    }

    /// <summary>Runtime content database: all defs, indexed by id. Plain C# (no ScriptableObject),
    /// so the Core layer stays engine-free and unit-testable. The Game layer populates this
    /// from ScriptableObjects/JSON at load.</summary>
    public sealed class ContentDb
    {
        private readonly Dictionary<string, TowerDef> _towers = new Dictionary<string, TowerDef>();
        private readonly Dictionary<string, EnemyDef> _enemies = new Dictionary<string, EnemyDef>();
        private readonly Dictionary<string, DifficultyDef> _difficulties = new Dictionary<string, DifficultyDef>();

        public void AddTower(TowerDef def) => _towers[def.Id] = def;
        public void AddEnemy(EnemyDef def) => _enemies[def.Id] = def;
        public void AddDifficulty(DifficultyDef def) => _difficulties[def.Id] = def;

        public bool TryGetTower(string id, out TowerDef def) => _towers.TryGetValue(id, out def);
        public bool TryGetEnemy(string id, out EnemyDef def) => _enemies.TryGetValue(id, out def);
        public bool TryGetDifficulty(string id, out DifficultyDef def) => _difficulties.TryGetValue(id, out def);

        public TowerDef GetTower(string id) =>
            _towers.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"Tower '{id}'");
        public EnemyDef GetEnemy(string id) =>
            _enemies.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"Enemy '{id}'");
        public DifficultyDef GetDifficulty(string id) =>
            _difficulties.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"Difficulty '{id}'");

        public IEnumerable<TowerDef> Towers => _towers.Values;
        public IEnumerable<EnemyDef> Enemies => _enemies.Values;
        public IEnumerable<DifficultyDef> Difficulties => _difficulties.Values;
        public bool HasEnemy(string id) => _enemies.ContainsKey(id);
    }
}
