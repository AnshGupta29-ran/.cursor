using System.Collections.Generic;
using NUnit.Framework;
using Tidewatch.Core;

namespace Tidewatch.Tests
{
    public class CombatTests
    {
        private GameSim MakeSim(out ContentDb db)
        {
            db = TestContent.MakeDb();
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(TestContent.MakeTideSchedule(), 1f);
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.Skitterling, 5, 0.5f, 0, 0f) } },
            };
            return new GameSim(db, grid, tide, waves, diff, "test", 1UL, false);
        }

        [Test]
        public void Tower_KillsEnemy_AndPaysBounty()
        {
            var sim = MakeSim(out var db);
            // Build a beacon spire right next to the causeway.
            Assert.IsTrue(sim.TryBuildTower(TowerIds.BeaconSpire, new GridPos(2, 0), out var err), err);
            int salvageAfterBuild = sim.Economy.Salvage;
            sim.TryCallWave();
            // Tick until the wave resolves.
            for (int i = 0; i < 2000 && sim.Enemies.Count > 0; i++) sim.Tick(0.05f);
            Assert.AreEqual(0, sim.Enemies.Count, "Tower should clear the skitterling wave");
            Assert.Greater(sim.Economy.Salvage, salvageAfterBuild, "Bounties should be paid");
        }

        [Test]
        public void ShroudedEnemy_NotTargetedWithoutLight()
        {
            var db = TestContent.MakeDb();
            var grid = TestContent.MakeGrid();
            grid.ApplyTidePhase(TidePhase.High); // water everywhere passable
            var tide = new TideSystem(new List<TidePhaseDuration>
                { new TidePhaseDuration(TidePhase.High, 100f) }, 1f);
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.AbyssalLurker, 1, 0.1f, 0, 0f) } },
            };
            var sim = new GameSim(db, grid, tide, waves, diff, "test", 1UL, false);
            // Build a non-light direct-fire tower (flare mortar) away from the Lantern aura.
            Assert.IsTrue(sim.TryBuildTower(TowerIds.FlareMortar, new GridPos(2, 0), out _));
            sim.TryCallWave();
            sim.Tick(0.1f);
            var lurker = sim.Enemies[0];
            Assert.IsTrue(lurker.ShroudedActive, "Lurker should be Shrouded in dark water");

            // Tick: the mortar must not damage the shrouded lurker.
            float hpBefore = lurker.Hp;
            for (int i = 0; i < 20; i++) sim.Tick(0.1f);
            Assert.AreEqual(hpBefore, lurker.Hp, "Direct-fire tower must not hit a Shrouded target");
        }

        [Test]
        public void ShroudedEnemy_RevealedByLight_BecomesTargetable()
        {
            var db = TestContent.MakeDb();
            // Place a beacon spire (light) on the plot so its illumination covers the causeway.
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(new List<TidePhaseDuration>
                { new TidePhaseDuration(TidePhase.High, 100f) }, 1f);
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.AbyssalLurker, 1, 0.1f, 0, 0f) } },
            };
            var sim = new GameSim(db, grid, tide, waves, diff, "test", 1UL, false);
            Assert.IsTrue(sim.TryBuildTower(TowerIds.BeaconSpire, new GridPos(2, 0), out _));
            sim.TryCallWave();
            // Tick: the beacon's light reveals the lurker as it enters range, then kills it.
            for (int i = 0; i < 4000 && sim.Enemies.Count > 0; i++) sim.Tick(0.05f);
            Assert.AreEqual(0, sim.Enemies.Count, "Illuminated lurker should be killable by the light tower");
        }

        [Test]
        public void Leak_ReducesLantern_AndDefeatAtZero()
        {
            var db = TestContent.MakeDb();
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(TestContent.MakeTideSchedule(), 1f);
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            diff.LanternLight = 2; // fragile lantern
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.Skitterling, 10, 0.1f, 0, 0f) } },
            };
            var sim = new GameSim(db, grid, tide, waves, diff, "test", 1UL, false);
            bool defeat = false;
            sim.Events.OnDefeat += () => defeat = true;
            sim.TryCallWave();
            // No towers; everything leaks. Tick until game over.
            for (int i = 0; i < 20000 && !sim.GameOver; i++) sim.Tick(0.1f);
            Assert.IsTrue(defeat, "Defeat should fire when Lantern Light reaches 0");
            Assert.AreEqual(0, sim.LanternLight);
        }

        [Test]
        public void Broodmother_SplitsOnDeath()
        {
            var db = TestContent.MakeDb();
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(TestContent.MakeTideSchedule(), 1f);
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            var sim = new GameSim(db, grid, tide, new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.Broodmother, 1, 0.1f, 0, 0f) } },
            }, diff, "test", 1UL, false);
            sim.TryCallWave();
            sim.Tick(0.1f);
            var brood = sim.Enemies[0];
            int countBefore = sim.Enemies.Count;
            sim.DamageEnemy(brood, 99999f, null, false);
            // After the kill, split children should be added.
            Assert.Greater(sim.Enemies.Count, countBefore - 1, "Broodmother should split into skitterlings");
        }

        [Test]
        public void DefeatTakesPrecedence_WhenLightHitsZeroAsLastEnemyDies()
        {
            // Documented rule: if Lantern Light hits 0 on the same tick the last enemy dies,
            // defeat wins. We simulate a lantern at 1 HP with one leaking enemy that is also
            // about to die — the leak resolves and fires defeat before any victory check.
            var db = TestContent.MakeDb();
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(TestContent.MakeTideSchedule(), 1f);
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            diff.LanternLight = 1;
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.Skitterling, 1, 0.1f, 0, 0f) } },
            };
            var sim = new GameSim(db, grid, tide, waves, diff, "test", 1UL, false);
            bool defeat = false, victory = false;
            sim.Events.OnDefeat += () => defeat = true;
            sim.Events.OnVictory += () => victory = true;
            sim.TryCallWave();
            for (int i = 0; i < 20000 && !sim.GameOver; i++) sim.Tick(0.1f);
            Assert.IsTrue(defeat);
            Assert.IsFalse(victory, "Victory must not fire when the lantern is already dark");
        }
    }
}
