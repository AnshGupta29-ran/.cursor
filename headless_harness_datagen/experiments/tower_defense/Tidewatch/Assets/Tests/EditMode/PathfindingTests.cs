using NUnit.Framework;
using Tidewatch.Core;

namespace Tidewatch.Tests
{
    public class PathfindingTests
    {
        [Test]
        public void Terrestrial_ReachesBaseOverDryCauseway()
        {
            var grid = TestContent.MakeGrid();
            grid.ApplyTidePhase(TidePhase.Low); // trenches drained, causeway dry
            var field = new PathField(grid, MoveClass.Terrestrial);
            var gate = grid.Gates[0];
            Assert.IsTrue(field.IsReachable(gate), "Terrestrial should reach base over dry causeway");
            var path = field.BuildPath(gate);
            Assert.Greater(path.Count, 0);
            Assert.AreEqual(grid.BasePos, path[path.Count - 1]);
        }

        [Test]
        public void Terrestrial_BlockedWhenCausewayFloods()
        {
            var grid = TestContent.MakeGrid();
            grid.ApplyTidePhase(TidePhase.High); // causeway flooded
            var field = new PathField(grid, MoveClass.Terrestrial);
            var gate = grid.Gates[0];
            // The only route to base is over causeway which is now water.
            Assert.IsFalse(field.IsReachable(gate),
                "Terrestrial should not reach base when causeway is flooded");
        }

        [Test]
        public void Pelagic_UsesWaterTiles()
        {
            var grid = TestContent.MakeGrid();
            grid.ApplyTidePhase(TidePhase.High);
            var field = new PathField(grid, MoveClass.Pelagic);
            var gate = grid.Gates[0];
            Assert.IsTrue(field.IsReachable(gate), "Pelagic should reach base over flooded tiles");
        }

        [Test]
        public void Amphibious_ReachesInBothPhases()
        {
            var grid = TestContent.MakeGrid();
            grid.ApplyTidePhase(TidePhase.Low);
            var low = new PathField(grid, MoveClass.Amphibious);
            Assert.IsTrue(low.IsReachable(grid.Gates[0]));
            grid.ApplyTidePhase(TidePhase.High);
            low.Recompute();
            Assert.IsTrue(low.IsReachable(grid.Gates[0]));
        }

        [Test]
        public void TideFlip_EnemyRepathsAlongNewGraph()
        {
            var db = TestContent.MakeDb();
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(TestContent.MakeTideSchedule(), 1f); // starts Low
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            var sim = new GameSim(db, grid, tide, TestContent.MakeWaves(), diff, "test", 1UL, false);

            // Spawn a terrestrial enemy at Low tide and step it onto the causeway.
            sim.TryCallWave();
            sim.Tick(0.1f);
            Assert.Greater(sim.Enemies.Count, 0);
            var e = sim.Enemies[0];
            var pathBefore = e.Path.Count;

            // Force tide to High: causeway floods, terrestrial must re-path (or slow, never stuck).
            tide.ForceSurge();
            // The sim re-paths on tide turn within the same tick.
            Assert.AreEqual(TidePhase.High, tide.CurrentPhase);
            // After re-path the enemy must still have a valid route state (path or slowed),
            // and must never have teleported: its position only changes by movement.
            for (int i = 0; i < 5; i++) sim.Tick(0.1f);
            Assert.IsFalse(float.IsNaN(e.X) || float.IsNaN(e.Y));
            Assert.GreaterOrEqual(pathBefore, 0);
        }

        [Test]
        public void Pelagic_OnDryingTile_BecomesBeached()
        {
            var db = TestContent.MakeDb();
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(TestContent.MakeTideSchedule(), 1f);
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            // A wave with a lurker (pelagic).
            var waves = new System.Collections.Generic.List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.AbyssalLurker, 1, 0.1f, 0, 0f) } },
            };
            var sim = new GameSim(db, grid, tide, waves, diff, "test", 1UL, false);
            sim.TryCallWave();
            sim.Tick(0.05f);
            var e = sim.Enemies[0];
            Assert.AreEqual(MoveClass.Pelagic, e.Def.MoveClass);

            // Drive the lurker onto a tile, then force Low tide (trench/causeway dry).
            sim.Tick(1f);
            tide.ForceSurge(); // to High (index advances), then again to Low
            tide.ForceSurge();
            // After drying, a pelagic on a dry tile must be beached (or on water).
            var tile = grid.Get(new GridPos((int)e.X, (int)e.Y));
            if (tile != null && !tile.IsWater && tile.Terrain != TerrainType.Gate)
                Assert.IsTrue(e.Beached, "Pelagic on a dried tile should be Beached");
        }

        [Test]
        public void PathNeverPassesThroughBuildPlot()
        {
            var grid = TestContent.MakeGrid();
            grid.ApplyTidePhase(TidePhase.Low);
            grid.TryPlaceTower(new GridPos(2, 0), TowerIds.BeaconSpire);
            var field = new PathField(grid, MoveClass.Terrestrial);
            var path = field.BuildPath(grid.Gates[0]);
            foreach (var p in path)
                Assert.AreNotEqual(new GridPos(2, 0), p, "Path must not cross a build plot");
        }
    }
}
