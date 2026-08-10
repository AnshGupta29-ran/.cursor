using System.Collections.Generic;
using NUnit.Framework;
using Tidewatch.Core;

namespace Tidewatch.Tests
{
    public class WaveTests
    {
        [Test]
        public void ValidWaveList_Passes()
        {
            var db = TestContent.MakeDb();
            var v = WaveSystem.Validate(TestContent.MakeWaves(), db, 1);
            Assert.IsTrue(v.Ok, v.ToString());
        }

        [Test]
        public void RejectsUnknownEnemyId()
        {
            var db = TestContent.MakeDb();
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry("kraken_that_does_not_exist", 3, 0.5f, 0, 0f) } },
            };
            var v = WaveSystem.Validate(waves, db, 1);
            Assert.IsFalse(v.Ok);
            StringAssert.Contains("unknown enemy id", v.ToString());
        }

        [Test]
        public void RejectsZeroCount()
        {
            var db = TestContent.MakeDb();
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.Skitterling, 0, 0.5f, 0, 0f) } },
            };
            var v = WaveSystem.Validate(waves, db, 1);
            Assert.IsFalse(v.Ok);
            StringAssert.Contains("count must be > 0", v.ToString());
        }

        [Test]
        public void RejectsBadGateIndex()
        {
            var db = TestContent.MakeDb();
            var waves = new List<WaveDef>
            {
                new WaveDef { Entries = { new SpawnEntry(EnemyIds.Skitterling, 3, 0.5f, 5, 0f) } },
            };
            var v = WaveSystem.Validate(waves, db, 1);
            Assert.IsFalse(v.Ok);
            StringAssert.Contains("gate index", v.ToString());
        }

        [Test]
        public void RejectsEmptyWaveList()
        {
            var db = TestContent.MakeDb();
            var v = WaveSystem.Validate(new List<WaveDef>(), db, 1);
            Assert.IsFalse(v.Ok);
        }

        [Test]
        public void SpawnSchedule_IsSeededAndOrdered()
        {
            var wave = new WaveDef
            {
                VarianceSeed = 1,
                Entries = { new SpawnEntry(EnemyIds.Skitterling, 10, 0.5f, 0, 1f) },
            };
            var a = WaveSystem.BuildSpawnSchedule(wave, new SeededRng(42));
            var b = WaveSystem.BuildSpawnSchedule(wave, new SeededRng(42));
            Assert.AreEqual(a.Count, b.Count, "Same seed must give same count");
            for (int i = 1; i < a.Count; i++)
                Assert.GreaterOrEqual(a[i].time, a[i - 1].time, "Schedule must be time-ordered");
        }
    }
}
