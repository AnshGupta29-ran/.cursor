namespace Tidewatch.Core
{
    /// <summary>
    /// Salvage economy. Tracks currency and computes bounties, wave bonuses, early-call
    /// bonuses, sell refunds, and the Keeper's Reserve interest dividend. Pure C#.
    ///
    /// Keeper's Reserve (design note): at each wave clear the player earns a small interest
    /// dividend on unspent Salvage. This creates a thrift-vs-spend tension — hoarding pays
    /// a capped dividend, but unbuilt towers deal no damage. Interest is capped so it can
    /// never out-compete actually building a defense.
    /// </summary>
    public sealed class Economy
    {
        public int Salvage { get; private set; }

        // Config (set from difficulty + global tuning).
        public float SellRefundRate = 0.70f;
        public float ReserveInterestRate = 0.04f;
        public int ReserveInterestCap = 40;
        public int WaveCompletionBonus = 30;
        /// <summary>Fraction of remaining wave time paid as early-call bonus per second.</summary>
        public float EarlyCallBonusPerSecond = 2f;
        public int EarlyCallBonusCap = 50;

        public Economy(int startingSalvage)
        {
            Salvage = startingSalvage;
        }

        public bool CanAfford(int cost) => Salvage >= cost;

        public bool TrySpend(int cost)
        {
            if (cost < 0 || Salvage < cost) return false;
            Salvage -= cost;
            return true;
        }

        public void AddSalvage(int amount)
        {
            if (amount > 0) Salvage += amount;
        }

        /// <summary>Bounty for a kill, after difficulty multiplier. Rounded down, min 1.</summary>
        public int KillBounty(EnemyDef def, float bountyMult)
        {
            int b = (int)(def.Bounty * bountyMult);
            return b < 1 ? 1 : b;
        }

        /// <summary>Refund when selling a tower for the total invested in it.</summary>
        public int SellRefund(int totalInvested) => (int)(totalInvested * SellRefundRate);

        /// <summary>
        /// Keeper's Reserve interest on current unspent Salvage, capped.
        /// Returns the dividend (which is also credited).
        /// </summary>
        public int PayReserveInterest()
        {
            int dividend = (int)(Salvage * ReserveInterestRate);
            if (dividend > ReserveInterestCap) dividend = ReserveInterestCap;
            if (dividend < 0) dividend = 0;
            Salvage += dividend;
            return dividend;
        }

        /// <summary>Early wave-call bonus based on how much spawn time was skipped.</summary>
        public int EarlyCallBonus(float remainingScheduledSeconds)
        {
            if (remainingScheduledSeconds <= 0f) return 0;
            int bonus = (int)(remainingScheduledSeconds * EarlyCallBonusPerSecond);
            return bonus > EarlyCallBonusCap ? EarlyCallBonusCap : bonus;
        }

        /// <summary>Set Salvage directly (used by save/load).</summary>
        public void SetSalvage(int amount) => Salvage = amount < 0 ? 0 : amount;
    }
}
