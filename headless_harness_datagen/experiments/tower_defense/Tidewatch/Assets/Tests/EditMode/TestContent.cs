using System.Collections.Generic;
using Tidewatch.Core;

namespace Tidewatch.Tests
{
    /// <summary>Shared fixtures: a content db and grid builders used across all tests.
    /// Pure logic — no scene loading, no timing.</summary>
    public static class TestContent
    {
        public static ContentDb MakeDb()
        {
            var db = new ContentDb();

            db.AddTower(new TowerDef
            {
                Id = TowerIds.BeaconSpire, DisplayName = "Beacon Spire",
                EmitsLight = true, DealsDamage = true, DirectFire = true, BonusVsBeached = 1f,
                Tiers = new[]
                {
                    new TowerTierStats { Damage = 8, Range = 4, FireRate = 1, IlluminationRadius = 3, Cost = 90 },
                    new TowerTierStats { Damage = 14, Range = 4.5f, FireRate = 1.1f, IlluminationRadius = 3.5f, Cost = 110 },
                    new TowerTierStats { Damage = 22, Range = 5, FireRate = 1.2f, IlluminationRadius = 4, Cost = 0 },
                },
                BranchA = new BranchDef { Id = "solar", DisplayName = "Solar Lance", DamageMult = 1.1f, BurstWindow = true, Cost = 160 },
                BranchB = new BranchDef { Id = "dusk", DisplayName = "Dusk Beam", AppliesSlowOnHit = true, Cost = 150 },
            });

            db.AddTower(new TowerDef
            {
                Id = TowerIds.PrismArray, DisplayName = "Prism Array",
                EmitsLight = false, DealsDamage = true, DirectFire = true, BonusVsBeached = 1f,
                Tiers = new[]
                {
                    new TowerTierStats { Damage = 6, Range = 3.5f, FireRate = 1.2f, ChainArcs = 2, Cost = 80 },
                    new TowerTierStats { Damage = 10, Range = 3.8f, FireRate = 1.3f, ChainArcs = 3, Cost = 100 },
                    new TowerTierStats { Damage = 16, Range = 4.2f, FireRate = 1.4f, ChainArcs = 4, Cost = 0 },
                },
                BranchA = new BranchDef { Id = "storm", ChainArcsDelta = 2, Cost = 150 },
                BranchB = new BranchDef { Id = "lens", DamageMult = 1.6f, ChainArcsDelta = -1, Cost = 150 },
            });

            db.AddTower(new TowerDef
            {
                Id = TowerIds.FlareMortar, DisplayName = "Flare Mortar",
                EmitsLight = false, DealsDamage = true, DirectFire = true, BonusVsBeached = 2f,
                Tiers = new[]
                {
                    new TowerTierStats { Damage = 18, Range = 5.5f, FireRate = 0.5f, Cost = 100 },
                    new TowerTierStats { Damage = 30, Range = 6f, FireRate = 0.55f, Cost = 130 },
                    new TowerTierStats { Damage = 46, Range = 6.5f, FireRate = 0.6f, Cost = 0 },
                },
                BranchA = new BranchDef { Id = "star", DamageMult = 1.25f, Cost = 170 },
                BranchB = new BranchDef { Id = "rapid", FireRateMult = 1.4f, Cost = 160 },
            });

            db.AddEnemy(new EnemyDef
            {
                Id = EnemyIds.Skitterling, DisplayName = "Skitterling",
                BaseHp = 20, BaseSpeed = 1.6f, Armor = 0, Bounty = 6, LeakDamage = 1,
                MoveClass = MoveClass.Terrestrial,
            });
            db.AddEnemy(new EnemyDef
            {
                Id = EnemyIds.BrineHulk, DisplayName = "Brine Hulk",
                BaseHp = 180, BaseSpeed = 0.55f, Armor = 4, Bounty = 22, LeakDamage = 3,
                MoveClass = MoveClass.Terrestrial,
            });
            db.AddEnemy(new EnemyDef
            {
                Id = EnemyIds.AbyssalLurker, DisplayName = "Abyssal Lurker",
                BaseHp = 90, BaseSpeed = 1f, Armor = 1, Bounty = 18, LeakDamage = 2,
                MoveClass = MoveClass.Pelagic, Shrouded = true,
            });
            db.AddEnemy(new EnemyDef
            {
                Id = EnemyIds.Broodmother, DisplayName = "Broodmother",
                BaseHp = 320, BaseSpeed = 0.6f, Armor = 2, Bounty = 40, LeakDamage = 5,
                MoveClass = MoveClass.Amphibious, SplitIntoId = EnemyIds.Skitterling, SplitCount = 4,
            });

            db.AddDifficulty(new DifficultyDef
            {
                Id = DifficultyIds.RisingGale, DisplayName = "Rising Gale",
                EnemyHpMult = 1f, EnemySpeedMult = 1f, BountyMult = 1f,
                StartingSalvage = 200, LanternLight = 20, TideCadenceMult = 1f, LeakMult = 1f,
            });

            return db;
        }

        /// <summary>A small grid: causeway row with a trench shortcut and one build plot.
        /// Layout (y up from bottom after parse):
        ///   y2: G C C C C B
        ///   y1: C T T T T C   (trench row)
        ///   y0: . . # . . .
        /// </summary>
        public static TileGrid MakeGrid()
        {
            var grid = new TileGrid(6, 3);
            // y = 2 (top lane)
            grid.SetTerrain(new GridPos(0, 2), TerrainType.Gate);
            for (int x = 1; x <= 4; x++) grid.SetTerrain(new GridPos(x, 2), TerrainType.Causeway);
            grid.SetTerrain(new GridPos(5, 2), TerrainType.Base);
            // y = 1 (trench row, connected vertically)
            grid.SetTerrain(new GridPos(0, 1), TerrainType.Causeway);
            for (int x = 1; x <= 4; x++) grid.SetTerrain(new GridPos(x, 1), TerrainType.Trench);
            grid.SetTerrain(new GridPos(5, 1), TerrainType.Causeway);
            // y = 0 (rock + one plot)
            grid.SetTerrain(new GridPos(2, 0), TerrainType.BuildPlot);
            return grid;
        }

        public static List<WaveDef> MakeWaves()
        {
            return new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.Skitterling, 3, 0.5f, 0, 0f) } },
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.Skitterling, 4, 0.5f, 0, 0f) } },
            };
        }

        public static List<TidePhaseDuration> MakeTideSchedule()
        {
            return new List<TidePhaseDuration>
            {
                new TidePhaseDuration(TidePhase.Low, 10f),
                new TidePhaseDuration(TidePhase.High, 10f),
            };
        }
    }
}
