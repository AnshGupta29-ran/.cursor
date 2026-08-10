using System.Collections.Generic;
using NUnit.Framework;
using Tidewatch.Core;

namespace Tidewatch.Tests
{
    public class TideTests
    {
        [Test]
        public void Tide_CyclesThroughSchedule()
        {
            var schedule = new List<TidePhaseDuration>
            {
                new TidePhaseDuration(TidePhase.Low, 5f),
                new TidePhaseDuration(TidePhase.Rising, 5f),
                new TidePhaseDuration(TidePhase.High, 5f),
            };
            var tide = new TideSystem(schedule, 1f);
            Assert.AreEqual(TidePhase.Low, tide.CurrentPhase);
            tide.Tick(5f);
            Assert.AreEqual(TidePhase.Rising, tide.CurrentPhase);
            tide.Tick(5f);
            Assert.AreEqual(TidePhase.High, tide.CurrentPhase);
            tide.Tick(5f);
            Assert.AreEqual(TidePhase.Low, tide.CurrentPhase, "Tide should wrap around the schedule");
        }

        [Test]
        public void Tide_CadenceMultiplier_ScalesDuration()
        {
            var schedule = new List<TidePhaseDuration> { new TidePhaseDuration(TidePhase.Low, 10f) };
            var slow = new TideSystem(schedule, 2f);
            Assert.AreEqual(20f, slow.CurrentPhaseDuration, "2x cadence should double phase duration");
        }

        [Test]
        public void TideTurn_FiresEvent()
        {
            var schedule = new List<TidePhaseDuration>
            {
                new TidePhaseDuration(TidePhase.Low, 1f),
                new TidePhaseDuration(TidePhase.High, 1f),
            };
            var tide = new TideSystem(schedule, 1f);
            TidePhase? fired = null;
            tide.OnPhaseTurn += p => fired = p;
            tide.Tick(1.1f);
            Assert.AreEqual(TidePhase.High, fired);
        }

        [Test]
        public void ForceSurge_AdvancesImmediately()
        {
            var schedule = new List<TidePhaseDuration>
            {
                new TidePhaseDuration(TidePhase.Low, 100f),
                new TidePhaseDuration(TidePhase.High, 100f),
            };
            var tide = new TideSystem(schedule, 1f);
            tide.ForceSurge();
            Assert.AreEqual(TidePhase.High, tide.CurrentPhase);
        }

        [Test]
        public void TilesFloodAndDrain_WithPhase()
        {
            var grid = TestContent.MakeGrid();
            var causeway = new GridPos(2, 2);
            var trench = new GridPos(2, 1);

            grid.ApplyTidePhase(TidePhase.Low);
            Assert.IsFalse(grid.Get(causeway).IsWater, "Causeway dry at Low");
            Assert.IsFalse(grid.Get(trench).IsWater, "Trench drained at Low");

            grid.ApplyTidePhase(TidePhase.High);
            Assert.IsTrue(grid.Get(causeway).IsWater, "Causeway floods at High");
            Assert.IsTrue(grid.Get(trench).IsWater, "Trench flooded at High");
        }

        [Test]
        public void BossTidecall_ForcesSurgeOnInterval()
        {
            var db = TestContent.MakeDb();
            // A boss def with a short tidecall interval.
            db.AddEnemy(new EnemyDef
            {
                Id = EnemyIds.DrownedBell, DisplayName = "The Drowned Bell",
                BaseHp = 4000, BaseSpeed = 0.35f, Armor = 6, Bounty = 400, LeakDamage = 10,
                MoveClass = MoveClass.Amphibious, TidecallInterval = 1.0f, IsBoss = true,
            });
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(TestContent.MakeTideSchedule(), 1f); // starts Low
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.DrownedBell, 1, 0.1f, 0, 0f) } },
            };
            var sim = new GameSim(db, grid, tide, waves, diff, "test", 1UL, false);
            int calls = 0;
            sim.Events.OnTidecall += () => calls++;
            sim.TryCallWave();
            // Tick past the tidecall interval; the boss should force at least one surge.
            for (int i = 0; i < 20; i++) sim.Tick(0.1f);
            Assert.GreaterOrEqual(calls, 1, "Boss should force a Tidecall surge on its interval");
        }

        [Test]
        public void TideState_RoundTrips()
        {
            var schedule = TestContent.MakeTideSchedule();
            var tide = new TideSystem(schedule, 1f);
            tide.Tick(12f); // into the second phase
            int idx = tide.CurrentIndex;
            float clock = tide.PhaseClock;
            var restored = new TideSystem(schedule, 1f);
            restored.SetState(idx, clock);
            Assert.AreEqual(tide.CurrentPhase, restored.CurrentPhase);
            Assert.AreEqual(clock, restored.PhaseClock, 1e-4f);
        }
    }
}
