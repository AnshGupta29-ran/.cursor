using System;
using System.Collections.Generic;
using System.IO;
using Tidewatch.Core;
using UnityEngine;

namespace Tidewatch.Game
{
    /// <summary>Adapts Unity's JsonUtility to the engine-free save store.</summary>
    public sealed class UnityJson : Tidewatch.Core.IJsonSerializer
    {
        public string Serialize<T>(T obj) => JsonUtility.ToJson(obj, true);
        public T Deserialize<T>(string json) => JsonUtility.FromJson<T>(json);
    }

    // ---- JSON DTOs (mirror the StreamingAssets content schema) ----

    [Serializable] public class TierJson
    {
        public float damage; public float range; public float fireRate;
        public float illuminationRadius; public float slowPct; public float armorShred;
        public int chainArcs; public int pierce; public int cost;
    }
    [Serializable] public class BranchJson
    {
        public string id; public string displayName; public string description;
        public float damageMult = 1f; public float rangeMult = 1f; public float fireRateMult = 1f;
        public float illuminationMult = 1f; public float slowPctDelta; public float armorShredDelta;
        public int chainArcsDelta; public int pierceDelta;
        public bool appliesSlowOnHit; public bool burstWindow; public int cost;
    }
    [Serializable] public class TowerJson
    {
        public string id; public string displayName; public string description;
        public bool emitsLight; public bool dealsDamage; public bool directFire; public float bonusVsBeached;
        public TierJson[] tiers; public BranchJson branchA; public BranchJson branchB;
    }
    [Serializable] public class TowerListJson { public TowerJson[] towers; }

    [Serializable] public class EnemyJson
    {
        public string id; public string displayName;
        public float baseHp; public float baseSpeed; public float armor;
        public int bounty; public int leakDamage; public string moveClass;
        public bool shrouded; public float spitInterval; public float spitDisableDuration;
        public string splitIntoId; public int splitCount; public float tidecallInterval; public bool isBoss;
    }
    [Serializable] public class EnemyListJson { public EnemyJson[] enemies; }

    [Serializable] public class DifficultyJson
    {
        public string id; public string displayName;
        public float enemyHpMult; public float enemySpeedMult; public float bountyMult;
        public int startingSalvage; public int lanternLight; public float tideCadenceMult; public float leakMult;
    }
    [Serializable] public class DifficultyListJson { public DifficultyJson[] difficulties; }

    [Serializable] public class TidePhaseJson { public string phase; public float seconds; }
    [Serializable] public class SpawnEntryJson
    {
        public string enemyId; public int count; public float interval; public int gate; public float delay;
    }
    [Serializable] public class WaveJson { public SpawnEntryJson[] entries; public int varianceSeed; }
    [Serializable] public class LevelJson
    {
        public string id; public string displayName; public string briefing;
        public string[] expectedEnemies; public float parTimeSeconds;
        public TidePhaseJson[] tideSchedule; public string[] grid; public WaveJson[] waves;
    }

    /// <summary>One fully-parsed level: grid + tide schedule + waves, ready for the sim.</summary>
    public sealed class LevelData
    {
        public string Id;
        public string DisplayName;
        public string Briefing;
        public string[] ExpectedEnemies;
        public float ParTime;
        public TileGrid Grid;
        public List<TidePhaseDuration> TideSchedule;
        public List<WaveDef> Waves;
    }

    /// <summary>
    /// Loads all content from StreamingAssets/Content as JSON and builds the engine-free
    /// ContentDb + LevelData. Adding a new tower/enemy/level = adding a JSON file here;
    /// zero C# changes required (levels are discovered by scanning the Levels directory).
    /// </summary>
    public static class ContentLoader
    {
        public static string ContentRoot => Path.Combine(Application.streamingAssetsPath, "Content");

        public static ContentDb LoadDb()
        {
            var db = new ContentDb();
            foreach (var t in LoadTowers()) db.AddTower(t);
            foreach (var e in LoadEnemies()) db.AddEnemy(e);
            foreach (var d in LoadDifficulties()) db.AddDifficulty(d);
            return db;
        }

        public static List<TowerDef> LoadTowers()
        {
            var list = new List<TowerDef>();
            string path = Path.Combine(ContentRoot, "towers.json");
            var data = JsonUtility.FromJson<TowerListJson>(File.ReadAllText(path));
            foreach (var j in data.towers)
            {
                var def = new TowerDef
                {
                    Id = j.id, DisplayName = j.displayName, Description = j.description,
                    EmitsLight = j.emitsLight, DealsDamage = j.dealsDamage, DirectFire = j.directFire,
                    BonusVsBeached = j.bonusVsBeached <= 0f ? 1f : j.bonusVsBeached,
                    Tiers = ConvertTiers(j.tiers),
                    BranchA = ConvertBranch(j.branchA),
                    BranchB = ConvertBranch(j.branchB),
                };
                list.Add(def);
            }
            return list;
        }

        private static TowerTierStats[] ConvertTiers(TierJson[] tiers)
        {
            var arr = new TowerTierStats[tiers.Length];
            for (int i = 0; i < tiers.Length; i++)
            {
                var t = tiers[i];
                arr[i] = new TowerTierStats
                {
                    Damage = t.damage, Range = t.range, FireRate = t.fireRate,
                    IlluminationRadius = t.illuminationRadius, SlowPct = t.slowPct,
                    ArmorShred = t.armorShred, ChainArcs = t.chainArcs, Pierce = t.pierce, Cost = t.cost,
                };
            }
            return arr;
        }

        private static BranchDef ConvertBranch(BranchJson j)
        {
            if (j == null) return null;
            return new BranchDef
            {
                Id = j.id, DisplayName = j.displayName, Description = j.description,
                DamageMult = j.damageMult, RangeMult = j.rangeMult, FireRateMult = j.fireRateMult,
                IlluminationMult = j.illuminationMult, SlowPctDelta = j.slowPctDelta,
                ArmorShredDelta = j.armorShredDelta, ChainArcsDelta = j.chainArcsDelta,
                PierceDelta = j.pierceDelta, AppliesSlowOnHit = j.appliesSlowOnHit,
                BurstWindow = j.burstWindow, Cost = j.cost,
            };
        }

        public static List<EnemyDef> LoadEnemies()
        {
            var list = new List<EnemyDef>();
            string path = Path.Combine(ContentRoot, "enemies.json");
            var data = JsonUtility.FromJson<EnemyListJson>(File.ReadAllText(path));
            foreach (var j in data.enemies)
            {
                list.Add(new EnemyDef
                {
                    Id = j.id, DisplayName = j.displayName,
                    BaseHp = j.baseHp, BaseSpeed = j.baseSpeed, Armor = j.armor,
                    Bounty = j.bounty, LeakDamage = j.leakDamage,
                    MoveClass = ParseMoveClass(j.moveClass),
                    Shrouded = j.shrouded,
                    SpitInterval = j.spitInterval, SpitDisableDuration = j.spitDisableDuration,
                    SplitIntoId = string.IsNullOrEmpty(j.splitIntoId) ? null : j.splitIntoId,
                    SplitCount = j.splitCount, TidecallInterval = j.tidecallInterval, IsBoss = j.isBoss,
                });
            }
            return list;
        }

        public static List<DifficultyDef> LoadDifficulties()
        {
            var list = new List<DifficultyDef>();
            string path = Path.Combine(ContentRoot, "difficulties.json");
            var data = JsonUtility.FromJson<DifficultyListJson>(File.ReadAllText(path));
            foreach (var j in data.difficulties)
            {
                list.Add(new DifficultyDef
                {
                    Id = j.id, DisplayName = j.displayName,
                    EnemyHpMult = j.enemyHpMult, EnemySpeedMult = j.enemySpeedMult, BountyMult = j.bountyMult,
                    StartingSalvage = j.startingSalvage, LanternLight = j.lanternLight,
                    TideCadenceMult = j.tideCadenceMult, LeakMult = j.leakMult,
                });
            }
            return list;
        }

        /// <summary>Discover every level JSON in Content/Levels (sorted by filename).</summary>
        public static List<LevelData> LoadAllLevels(ContentDb db)
        {
            var levels = new List<LevelData>();
            string dir = Path.Combine(ContentRoot, "Levels");
            if (!Directory.Exists(dir)) return levels;
            var files = Directory.GetFiles(dir, "*.json");
            Array.Sort(files, StringComparer.Ordinal);
            foreach (var f in files)
            {
                var level = LoadLevel(f, db);
                if (level != null) levels.Add(level);
            }
            return levels;
        }

        public static LevelData LoadLevel(string path, ContentDb db)
        {
            var j = JsonUtility.FromJson<LevelJson>(File.ReadAllText(path));
            var grid = ParseGrid(j.grid);
            var schedule = new List<TidePhaseDuration>();
            foreach (var p in j.tideSchedule)
                schedule.Add(new TidePhaseDuration(ParsePhase(p.phase), p.seconds));
            var waves = new List<WaveDef>();
            foreach (var w in j.waves)
            {
                var wd = new WaveDef { VarianceSeed = w.varianceSeed };
                foreach (var e in w.entries)
                    wd.Entries.Add(new SpawnEntry(e.enemyId, e.count, e.interval, e.gate, e.delay));
                waves.Add(wd);
            }
            // Validate the wave list against content; log but still return so a designer
            // sees the error rather than a silent failure.
            var validation = WaveSystem.Validate(waves, db, grid.Gates.Count);
            if (!validation.Ok)
                Debug.LogError($"[Tidewatch] Level '{j.id}' wave validation failed:\n{validation}");

            return new LevelData
            {
                Id = j.id, DisplayName = j.displayName, Briefing = j.briefing,
                ExpectedEnemies = j.expectedEnemies, ParTime = j.parTimeSeconds,
                Grid = grid, TideSchedule = schedule, Waves = waves,
            };
        }

        /// <summary>
        /// Parse the ASCII grid. Legend:
        ///  ~ deep water   . rock   C causeway   T trench   # build plot   G gate   B base
        /// </summary>
        public static TileGrid ParseGrid(string[] rows)
        {
            int height = rows.Length;
            int width = 0;
            foreach (var r in rows) width = Math.Max(width, r.Length);
            var grid = new TileGrid(width, height);
            // Rows are authored top-to-bottom; flip so y=0 is the bottom row.
            for (int ry = 0; ry < height; ry++)
            {
                string row = rows[ry];
                int y = height - 1 - ry;
                for (int x = 0; x < row.Length; x++)
                {
                    char c = row[x];
                    var pos = new GridPos(x, y);
                    switch (c)
                    {
                        case '~': grid.SetTerrain(pos, TerrainType.DeepWater); break;
                        case 'C': grid.SetTerrain(pos, TerrainType.Causeway); break;
                        case 'T': grid.SetTerrain(pos, TerrainType.Trench); break;
                        case '#': grid.SetTerrain(pos, TerrainType.BuildPlot); break;
                        case 'G': grid.SetTerrain(pos, TerrainType.Gate); break;
                        case 'B': grid.SetTerrain(pos, TerrainType.Base); break;
                        default: grid.SetTerrain(pos, TerrainType.Rock); break;
                    }
                }
            }
            return grid;
        }

        private static MoveClass ParseMoveClass(string s)
        {
            switch (s)
            {
                case "Amphibious": return MoveClass.Amphibious;
                case "Pelagic": return MoveClass.Pelagic;
                default: return MoveClass.Terrestrial;
            }
        }

        private static TidePhase ParsePhase(string s)
        {
            switch (s)
            {
                case "Rising": return TidePhase.Rising;
                case "High": return TidePhase.High;
                case "Ebbing": return TidePhase.Ebbing;
                default: return TidePhase.Low;
            }
        }
    }
}
