using NUnit.Framework;
using Tidewatch.Core;

namespace Tidewatch.Tests
{
    public class UpgradeTests
    {
        [Test]
        public void Upgrade_AdvancesTier_AndDeductsCost()
        {
            var db = TestContent.MakeDb();
            var eco = new Economy(1000);
            var def = db.GetTower(TowerIds.BeaconSpire);
            var t = new TowerInstance(def, new GridPos(0, 0), false);
            Assert.AreEqual(0, t.Tier);
            float baseDmg = t.ResolveStats().Damage;

            Assert.IsTrue(t.TryUpgrade(eco));
            Assert.AreEqual(1, t.Tier);
            Assert.Greater(t.ResolveStats().Damage, baseDmg);
            Assert.AreEqual(1000 - 110, eco.Salvage);
        }

        [Test]
        public void Upgrade_FailsWhenBroke()
        {
            var db = TestContent.MakeDb();
            var eco = new Economy(10);
            var t = new TowerInstance(db.GetTower(TowerIds.BeaconSpire), new GridPos(0, 0), false);
            Assert.IsFalse(t.TryUpgrade(eco));
            Assert.AreEqual(0, t.Tier);
        }

        [Test]
        public void Tier3_RequiresBranchChoice()
        {
            var db = TestContent.MakeDb();
            var eco = new Economy(1000);
            var t = new TowerInstance(db.GetTower(TowerIds.BeaconSpire), new GridPos(0, 0), false);
            t.TryUpgrade(eco); // tier 2
            t.TryUpgrade(eco); // tier 3 (index 2)
            Assert.AreEqual(2, t.Tier);
            Assert.IsTrue(t.NeedsBranchChoice);
            Assert.AreEqual(-1, t.NextUpgradeCost, "No further linear upgrade at tier 3");
        }

        [Test]
        public void BranchChoice_IsMutuallyExclusive_AndAppliesStats()
        {
            var db = TestContent.MakeDb();
            var eco = new Economy(1000);
            var t = new TowerInstance(db.GetTower(TowerIds.BeaconSpire), new GridPos(0, 0), false);
            t.TryUpgrade(eco);
            t.TryUpgrade(eco);
            float t3Dmg = t.ResolveStats().Damage;

            Assert.IsTrue(t.TryPickBranch(true, eco)); // Solar Lance: +10% dmg
            Assert.IsNotNull(t.BranchId);
            Assert.Greater(t.ResolveStats().Damage, t3Dmg);

            // Second branch must be rejected.
            Assert.IsFalse(t.TryPickBranch(false, eco));
        }

        [Test]
        public void Prism_Resonance_AddsArcPerAdjacentPrism()
        {
            var db = TestContent.MakeDb();
            var solo = new TowerInstance(db.GetTower(TowerIds.PrismArray), new GridPos(0, 0), false);
            var adjacent = new TowerInstance(db.GetTower(TowerIds.PrismArray), new GridPos(1, 0), true);
            Assert.AreEqual(solo.ResolveStats().ChainArcs + 1, adjacent.ResolveStats().ChainArcs);
        }

        [Test]
        public void BranchDeltas_StackOnTier3()
        {
            var db = TestContent.MakeDb();
            var eco = new Economy(1000);
            var t = new TowerInstance(db.GetTower(TowerIds.PrismArray), new GridPos(0, 0), false);
            t.TryUpgrade(eco);
            t.TryUpgrade(eco);
            int baseArcs = t.ResolveStats().ChainArcs;
            t.TryPickBranch(true, eco); // Storm Lattice: +2 arcs
            Assert.AreEqual(baseArcs + 2, t.ResolveStats().ChainArcs);
        }

        [Test]
        public void TotalInvested_TrackedForRefund()
        {
            var db = TestContent.MakeDb();
            var eco = new Economy(1000);
            var t = new TowerInstance(db.GetTower(TowerIds.BeaconSpire), new GridPos(0, 0), false);
            Assert.AreEqual(90, t.TotalInvested);
            t.TryUpgrade(eco);
            Assert.AreEqual(90 + 110, t.TotalInvested);
        }
    }
}
