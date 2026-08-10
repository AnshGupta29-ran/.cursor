using System.Collections.Generic;
using NUnit.Framework;
using Tidewatch.Core;

namespace Tidewatch.Tests
{
    public class SaveTests
    {
        private sealed class TestJson : Tidewatch.Core.IJsonSerializer
        {
            public string Serialize<T>(T obj) => UnityEngine.JsonUtility.ToJson(obj);
            public T Deserialize<T>(string json) => UnityEngine.JsonUtility.FromJson<T>(json);
        }

        private string _dir;

        [SetUp]
        public void SetUp()
        {
            _dir = System.IO.Path.Combine(System.IO.Path.GetTempPath(),
                "tidewatch_test_" + System.Guid.NewGuid().ToString("N"));
        }

        [TearDown]
        public void TearDown()
        {
            try { if (System.IO.Directory.Exists(_dir)) System.IO.Directory.Delete(_dir, true); }
            catch { /* best effort */ }
        }

        [Test]
        public void SaveRoundTrip_PreservesRunState()
        {
            var db = TestContent.MakeDb();
            var grid = TestContent.MakeGrid();
            var tide = new TideSystem(TestContent.MakeTideSchedule(), 1f);
            var diff = db.GetDifficulty(DifficultyIds.RisingGale);
            var sim = new GameSim(db, grid, tide, TestContent.MakeWaves(), diff, "level_test", 123UL, false);

            // Build a tower and advance a wave so there's real state to save.
            sim.TryBuildTower(TowerIds.BeaconSpire, new GridPos(2, 0), out _);
            sim.TryCallWave();
            for (int i = 0; i < 50; i++) sim.Tick(0.1f); // clear wave 1
            int salvageBefore = sim.Economy.Salvage;
            int waveBefore = sim.NextWaveIndex;

            var store = new SaveStore(_dir, new TestJson());
            store.SaveRun(0, sim.ToSave());

            var loaded = store.TryLoadRun(0, out var err);
            Assert.IsNull(err);
            Assert.IsNotNull(loaded);
            Assert.AreEqual(123UL, loaded.runSeed);
            Assert.AreEqual("level_test", loaded.levelId);
            Assert.AreEqual(waveBefore, loaded.waveIndex);
            Assert.AreEqual(salvageBefore, loaded.salvage);
            Assert.AreEqual(1, loaded.towers.Count);
            Assert.AreEqual(TowerIds.BeaconSpire, loaded.towers[0].defId);

            // Rebuild a sim from the save and confirm the tower comes back.
            var sim2 = GameSim.FromSave(loaded, db, TestContent.MakeGrid(),
                new TideSystem(TestContent.MakeTideSchedule(), 1f), TestContent.MakeWaves(), diff);
            Assert.AreEqual(1, sim2.Towers.Count);
            Assert.AreEqual(salvageBefore, sim2.Economy.Salvage);
        }

        [Test]
        public void CorruptedSave_ReturnsError_NotCrash()
        {
            var store = new SaveStore(_dir, new TestJson());
            System.IO.File.WriteAllText(store.SlotPath(1), "{ this is not valid json !!!");
            var loaded = store.TryLoadRun(1, out var err);
            Assert.IsNull(loaded);
            Assert.IsNotEmpty(err);
        }

        [Test]
        public void WrongVersionSave_IsRejected()
        {
            var store = new SaveStore(_dir, new TestJson());
            var save = new RunSave { version = SaveSchema.CurrentVersion + 99 };
            System.IO.File.WriteAllText(store.SlotPath(2), new TestJson().Serialize(save));
            var loaded = store.TryLoadRun(2, out var err);
            Assert.IsNull(loaded);
            StringAssert.Contains("version", err);
        }

        [Test]
        public void MissingSlot_ReportsNoSave()
        {
            var store = new SaveStore(_dir, new TestJson());
            var loaded = store.TryLoadRun(0, out var err);
            Assert.IsNull(loaded);
            Assert.IsNotEmpty(err);
        }

        [Test]
        public void MetaProgress_TracksUnlocksAndRecords()
        {
            var store = new SaveStore(_dir, new TestJson());
            var meta = new MetaProgress();
            meta.unlockedLevels.Add("level_01");
            var rec = meta.GetOrAddRecord("level_01", DifficultyIds.RisingGale);
            rec.cleared = true;
            rec.bestWaveReached = 12;
            store.SaveMeta(meta);

            var loaded = store.LoadMeta();
            Assert.IsTrue(loaded.IsUnlocked("level_01"));
            var r = loaded.GetOrAddRecord("level_01", DifficultyIds.RisingGale);
            Assert.IsTrue(r.cleared);
            Assert.AreEqual(12, r.bestWaveReached);
        }
    }
}
