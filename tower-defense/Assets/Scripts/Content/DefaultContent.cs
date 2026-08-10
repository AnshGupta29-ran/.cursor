using System.Collections.Generic;
using UnityEngine;

namespace TD.Content
{
    /// <summary>
    /// Builds the game's content in code so a fresh clone is playable without
    /// hand-authored .asset files. The editor setup wizard writes these out as
    /// ScriptableObject assets for designers to tweak.
    /// </summary>
    public static class DefaultContent
    {
        // ------------------------------------------------------------------
        // Enemies
        // ------------------------------------------------------------------
        public static List<EnemyDefinition> CreateEnemies()
        {
            return new List<EnemyDefinition>
            {
                NewEnemy("runner", "Runner", EnemyClass.Runner,
                    health: 28, speed: 1.5f, armor: 0f, reward: 6, lives: 1,
                    color: new Color(0.85f, 0.35f, 0.30f), scale: 0.85f),

                NewEnemy("soldier", "Soldier", EnemyClass.Soldier,
                    health: 85, speed: 1.0f, armor: 0f, reward: 11, lives: 1,
                    color: new Color(0.75f, 0.30f, 0.55f), scale: 1.0f),

                NewEnemy("tank", "Tank", EnemyClass.Tank,
                    health: 320, speed: 0.55f, armor: 0.30f, reward: 26, lives: 2,
                    color: new Color(0.50f, 0.28f, 0.20f), scale: 1.4f),

                NewEnemy("swift", "Swift", EnemyClass.Swift,
                    health: 38, speed: 2.5f, armor: 0f, reward: 12, lives: 1,
                    color: new Color(0.35f, 0.80f, 0.85f), scale: 0.75f),

                NewEnemy("flyer", "Flyer", EnemyClass.Flyer,
                    health: 95, speed: 1.6f, armor: 0f, reward: 16, lives: 1,
                    color: new Color(0.95f, 0.80f, 0.30f), scale: 0.9f, flying: true),

                NewEnemy("boss", "Warlord", EnemyClass.Boss,
                    health: 2200, speed: 0.5f, armor: 0.20f, reward: 160, lives: 5,
                    color: new Color(0.30f, 0.10f, 0.35f), scale: 2.1f),
            };
        }

        static EnemyDefinition NewEnemy(
            string id, string name, EnemyClass cls,
            float health, float speed, float armor, int reward, int lives,
            Color color, float scale, bool flying = false)
        {
            var e = ScriptableObject.CreateInstance<EnemyDefinition>();
            e.id = id; e.displayName = name; e.enemyClass = cls;
            e.health = health; e.moveSpeed = speed; e.armor = armor;
            e.reward = reward; e.livesCost = lives;
            e.color = color; e.scale = scale; e.flying = flying;
            return e;
        }

        // ------------------------------------------------------------------
        // Towers — 4 types, each with a 3-level upgrade path
        // ------------------------------------------------------------------
        public static List<TowerDefinition> CreateTowers()
        {
            return new List<TowerDefinition> { Arrow(), Cannon(), Frost(), Sniper() };
        }

        static TowerDefinition NewTower(string id, string name, string desc, string hint,
            Targeting targeting, params TowerLevel[] levels)
        {
            var t = ScriptableObject.CreateInstance<TowerDefinition>();
            t.id = id; t.displayName = name; t.description = desc; t.upgradeHint = hint;
            t.targeting = targeting; t.levels = levels;
            return t;
        }

        static TowerDefinition Arrow() => NewTower(
            "arrow", "Arrow Tower",
            "Reliable single-target shots. Cheap and quick.",
            "Upgrades: more damage, range and fire rate.",
            Targeting.First,
            new TowerLevel { cost = 50, damage = 12, range = 2.4f, fireRate = 1.4f, projectileSpeed = 14f, bodyColor = new Color(0.35f, 0.65f, 0.40f) },
            new TowerLevel { cost = 75, damage = 20, range = 2.8f, fireRate = 1.7f, projectileSpeed = 16f, bodyColor = new Color(0.30f, 0.72f, 0.45f), scale = 1.1f },
            new TowerLevel { cost = 120, damage = 34, range = 3.2f, fireRate = 2.1f, projectileSpeed = 18f, bodyColor = new Color(0.20f, 0.80f, 0.50f), scale = 1.2f });

        static TowerDefinition Cannon() => NewTower(
            "cannon", "Cannon Tower",
            "Lobbed shells deal splash damage around the impact. Great against groups.",
            "Upgrades: bigger shells, wider splash, faster reload.",
            Targeting.First,
            new TowerLevel { cost = 90, damage = 26, range = 2.2f, fireRate = 0.6f, projectileSpeed = 8f, splashRadius = 0.9f, bodyColor = new Color(0.85f, 0.55f, 0.25f) },
            new TowerLevel { cost = 130, damage = 44, range = 2.4f, fireRate = 0.65f, projectileSpeed = 9f, splashRadius = 1.1f, bodyColor = new Color(0.90f, 0.45f, 0.20f), scale = 1.1f },
            new TowerLevel { cost = 190, damage = 72, range = 2.6f, fireRate = 0.7f, projectileSpeed = 10f, splashRadius = 1.35f, bodyColor = new Color(0.95f, 0.35f, 0.15f), scale = 1.2f });

        static TowerDefinition Frost() => NewTower(
            "frost", "Frost Tower",
            "Chills enemies it hits, slowing their advance. Low damage, high utility.",
            "Upgrades: stronger slow, longer chill, wider reach.",
            Targeting.First,
            new TowerLevel { cost = 70, damage = 5, range = 2.3f, fireRate = 1.1f, projectileSpeed = 12f, slowAmount = 0.30f, slowDuration = 1.6f, bodyColor = new Color(0.40f, 0.70f, 0.95f) },
            new TowerLevel { cost = 100, damage = 8, range = 2.6f, fireRate = 1.2f, projectileSpeed = 13f, slowAmount = 0.40f, slowDuration = 2.0f, bodyColor = new Color(0.35f, 0.80f, 1.00f), scale = 1.1f },
            new TowerLevel { cost = 150, damage = 12, range = 3.0f, fireRate = 1.3f, projectileSpeed = 14f, slowAmount = 0.50f, slowDuration = 2.5f, bodyColor = new Color(0.30f, 0.90f, 1.00f), scale = 1.2f });

        static TowerDefinition Sniper() => NewTower(
            "sniper", "Sniper Tower",
            "Long range rail shots that punch through armor. Slow but devastating.",
            "Upgrades: huge damage spikes and extreme range.",
            Targeting.Strongest,
            new TowerLevel { cost = 120, damage = 55, range = 4.5f, fireRate = 0.4f, projectileSpeed = 30f, armorPierce = 0.5f, bodyColor = new Color(0.55f, 0.40f, 0.85f) },
            new TowerLevel { cost = 170, damage = 95, range = 5.2f, fireRate = 0.45f, projectileSpeed = 32f, armorPierce = 0.65f, bodyColor = new Color(0.60f, 0.45f, 0.90f), scale = 1.1f },
            new TowerLevel { cost = 250, damage = 165, range = 6.0f, fireRate = 0.5f, projectileSpeed = 34f, armorPierce = 0.8f, bodyColor = new Color(0.65f, 0.50f, 0.95f), scale = 1.2f });

        // ------------------------------------------------------------------
        // Levels — grid layouts, paths and wave compositions
        // ------------------------------------------------------------------
        public static List<LevelDefinition> CreateLevels(Dictionary<string, EnemyDefinition> enemies)
        {
            return new List<LevelDefinition>
            {
                Level1(enemies),
                Level2(enemies),
                Level3(enemies),
            };
        }

        static Vector2Int[] Rect(int x0, int y0, int x1, int y1)
        {
            var list = new List<Vector2Int>();
            for (int x = x0; x <= x1; x++)
                for (int y = y0; y <= y1; y++)
                    list.Add(new Vector2Int(x, y));
            return list.ToArray();
        }

        static Vector2Int[] Path(params int[] coords)
        {
            var list = new List<Vector2Int>();
            for (int i = 0; i + 1 < coords.Length; i += 2)
                list.Add(new Vector2Int(coords[i], coords[i + 1]));
            return list.ToArray();
        }

        static Wave W(string label, params WaveEntry[] entries) => new Wave { label = label, entries = entries };
        static WaveEntry E(EnemyDefinition e, int count, float interval = 0.9f, float delay = 0f, float hp = 1f)
            => new WaveEntry { enemy = e, count = count, interval = interval, startDelay = delay, healthScale = hp };

        static LevelDefinition Level1(Dictionary<string, EnemyDefinition> en)
        {
            var level = ScriptableObject.CreateInstance<LevelDefinition>();
            level.id = "level1"; level.displayName = "Greenfield Pass";
            level.description = "A gentle S-curve through open fields. Learn the ropes.";
            level.startGold = 160; level.startLives = 20; level.goldTrickle = 2f;
            level.wavesNeeded = 10;
            level.gridWidth = 10; level.gridHeight = 8; level.cellSize = 1f;
            level.pathPoints = Path(0, 6, 4, 6, 4, 2, 8, 2, 8, 6, 9, 6);
            level.buildNodes = Concat(
                Rect(1, 3, 3, 5), Rect(2, 1, 3, 1), Rect(5, 3, 7, 4),
                Rect(6, 6, 7, 6), Rect(6, 1, 7, 1));
            level.waves = NewWaves(
                W("Scouts", E(en["runner"], 6)),
                W("More Scouts", E(en["runner"], 9, 0.8f)),
                W("Infantry", E(en["soldier"], 6)),
                W("Mixed Patrol", E(en["runner"], 8, 0.7f), E(en["soldier"], 5, 1f, 2f)),
                W("Armored Push", E(en["tank"], 3, 1.4f), E(en["runner"], 8, 0.6f, 3f)),
                W("Wings", E(en["flyer"], 6)),
                W("Swarm", E(en["runner"], 16, 0.45f)),
                W("Heavy Infantry", E(en["soldier"], 10, 0.8f), E(en["tank"], 3, 1.6f, 4f)),
                W("Sky Assault", E(en["flyer"], 9, 0.7f), E(en["swift"], 6, 0.5f, 3f)),
                W("The Warlord", E(en["boss"], 1), E(en["soldier"], 8, 0.8f, 4f)));
            return level;
        }

        static LevelDefinition Level2(Dictionary<string, EnemyDefinition> en)
        {
            var level = ScriptableObject.CreateInstance<LevelDefinition>();
            level.id = "level2"; level.displayName = "Twin Forks";
            level.description = "Two long lanes mean towers cover the middle twice.";
            level.startGold = 180; level.startLives = 20; level.goldTrickle = 2.2f;
            level.wavesNeeded = 12;
            level.gridWidth = 12; level.gridHeight = 9; level.cellSize = 1f;
            level.pathPoints = Path(0, 1, 10, 1, 10, 7, 2, 7, 2, 4, 11, 4);
            level.buildNodes = Concat(
                Rect(1, 2, 3, 3), Rect(5, 2, 7, 3), Rect(4, 5, 6, 6),
                Rect(8, 5, 9, 6), Rect(1, 5, 1, 6), Rect(5, 8, 8, 8));
            level.waves = NewWaves(
                W("Vanguard", E(en["runner"], 8, 0.8f)),
                W("Fast Movers", E(en["swift"], 6)),
                W("Infantry Column", E(en["soldier"], 8, 0.8f)),
                W("Ironclad", E(en["tank"], 4, 1.3f), E(en["runner"], 10, 0.5f, 3f)),
                W("Air Raid", E(en["flyer"], 8, 0.7f)),
                W("Blitz", E(en["swift"], 10, 0.4f), E(en["runner"], 10, 0.4f, 2f)),
                W("Phalanx", E(en["soldier"], 12, 0.7f)),
                W("Combined Arms", E(en["tank"], 5, 1.2f), E(en["flyer"], 6, 0.8f, 3f)),
                W("Storm", E(en["swift"], 14, 0.35f)),
                W("Siege", E(en["tank"], 7, 1.1f), E(en["soldier"], 8, 0.8f, 4f)),
                W("Full Force", E(en["flyer"], 8, 0.6f), E(en["swift"], 10, 0.4f, 2f), E(en["tank"], 4, 1.4f, 5f)),
                W("Twin Warlords", E(en["boss"], 2, 4f), E(en["soldier"], 10, 0.7f, 5f)));
            return level;
        }

        static LevelDefinition Level3(Dictionary<string, EnemyDefinition> en)
        {
            var level = ScriptableObject.CreateInstance<LevelDefinition>();
            level.id = "level3"; level.displayName = "Spiral Keep";
            level.description = "The path coils inward — every second counts at the core.";
            level.startGold = 220; level.startLives = 15; level.goldTrickle = 2.5f;
            level.wavesNeeded = 14;
            level.gridWidth = 12; level.gridHeight = 11; level.cellSize = 1f;
            level.pathPoints = Path(0, 9, 10, 9, 10, 1, 2, 1, 2, 7, 8, 7, 8, 3, 5, 3, 5, 5);
            level.buildNodes = Concat(
                Rect(1, 2, 1, 8), Rect(3, 2, 4, 2), Rect(6, 2, 7, 2),
                Rect(3, 8, 7, 8), Rect(3, 3, 4, 6), Rect(6, 4, 7, 6),
                Rect(9, 2, 9, 8), Rect(11, 1, 11, 10));
            level.waves = NewWaves(
                W("Probe", E(en["runner"], 10, 0.7f)),
                W("Raiders", E(en["swift"], 8, 0.5f)),
                W("Shield Wall", E(en["soldier"], 10, 0.7f)),
                W("Air Wing", E(en["flyer"], 8, 0.7f)),
                W("Battering Ram", E(en["tank"], 5, 1.2f), E(en["runner"], 12, 0.4f, 3f)),
                W("Whirlwind", E(en["swift"], 14, 0.35f)),
                W("Crusade", E(en["soldier"], 14, 0.6f)),
                W("Skyfall", E(en["flyer"], 12, 0.5f)),
                W("Juggernauts", E(en["tank"], 8, 1f)),
                W("Flood", E(en["runner"], 22, 0.3f)),
                W("Steel & Storm", E(en["tank"], 6, 1.1f), E(en["swift"], 12, 0.35f, 3f)),
                W("Air Armada", E(en["flyer"], 14, 0.45f), E(en["boss"], 1, 0f, 6f)),
                W("Last March", E(en["soldier"], 16, 0.5f), E(en["tank"], 8, 0.9f, 4f)),
                W("The Three Kings", E(en["boss"], 3, 3.5f), E(en["swift"], 16, 0.3f, 5f)));
            return level;
        }

        static WaveConfig NewWaves(params Wave[] waves)
        {
            var cfg = ScriptableObject.CreateInstance<WaveConfig>();
            cfg.healthScalePerWave = 0.08f;
            cfg.waves = waves;
            return cfg;
        }

        static Vector2Int[] Concat(params Vector2Int[][] arrays)
        {
            var list = new List<Vector2Int>();
            foreach (var a in arrays) list.AddRange(a);
            return list.ToArray();
        }
    }
}
