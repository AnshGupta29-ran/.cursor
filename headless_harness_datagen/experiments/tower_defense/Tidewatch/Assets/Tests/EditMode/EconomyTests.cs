using NUnit.Framework;
using Tidewatch.Core;

namespace Tidewatch.Tests
{
    public class EconomyTests
    {
        [Test]
        public void KillBounty_AppliesMultiplier_WithFloorAndMin()
        {
            var db = TestContent.MakeDb();
            var eco = new Economy(0);
            var skit = db.GetEnemy(EnemyIds.Skitterling); // bounty 6
            Assert.AreEqual(6, eco.KillBounty(skit, 1f));
            Assert.AreEqual(3, eco.KillBounty(skit, 0.5f));
            // Min 1 even at tiny multiplier.
            Assert.AreEqual(1, eco.KillBounty(skit, 0.01f));
        }

        [Test]
        public void ReserveInterest_IsCapped()
        {
            var eco = new Economy(10000) { ReserveInterestRate = 0.04f, ReserveInterestCap = 40 };
            int dividend = eco.PayReserveInterest();
            Assert.AreEqual(40, dividend, "Interest must be capped");
            Assert.AreEqual(10040, eco.Salvage);
        }

        [Test]
        public void ReserveInterest_ProportionalBelowCap()
        {
            var eco = new Economy(500) { ReserveInterestRate = 0.04f, ReserveInterestCap = 40 };
            int dividend = eco.PayReserveInterest();
            Assert.AreEqual(20, dividend);
            Assert.AreEqual(520, eco.Salvage);
        }

        [Test]
        public void SellRefund_UsesRefundRate()
        {
            var eco = new Economy(0) { SellRefundRate = 0.70f };
            Assert.AreEqual(70, eco.SellRefund(100));
            Assert.AreEqual(0, eco.SellRefund(0));
        }

        [Test]
        public void TrySpend_RespectsBalance()
        {
            var eco = new Economy(100);
            Assert.IsFalse(eco.TrySpend(150));
            Assert.IsTrue(eco.TrySpend(60));
            Assert.AreEqual(40, eco.Salvage);
        }

        [Test]
        public void EarlyCallBonus_ScalesWithSkippedTime_AndCaps()
        {
            var eco = new Economy(0) { EarlyCallBonusPerSecond = 2f, EarlyCallBonusCap = 50 };
            Assert.AreEqual(20, eco.EarlyCallBonus(10f));
            Assert.AreEqual(50, eco.EarlyCallBonus(100f)); // capped
            Assert.AreEqual(0, eco.EarlyCallBonus(0f));
        }
    }
}
