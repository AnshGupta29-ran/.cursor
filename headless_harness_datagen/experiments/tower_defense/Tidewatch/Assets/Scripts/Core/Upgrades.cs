namespace Tidewatch.Core
{
    /// <summary>
    /// Tower instance state + upgrade/branch math. Pure C# so it is EditMode-testable.
    /// Tiers are 0-indexed internally (tier 0 = "tier 1" in the design doc / UI).
    /// Tier 3 (index 2) is a branch choice between two mutually exclusive capstones.
    /// </summary>
    public sealed class TowerInstance
    {
        public string DefId;
        public GridPos Plot;
        public int Tier;               // 0,1,2
        public string BranchId;        // null until tier 3 chosen; BranchA.Id or BranchB.Id
        public TargetPriority Priority = TargetPriority.First;
        public int TotalInvested;      // for sell refunds
        public float DisabledTimer;    // >0 while disabled by a Spitter
        // Beacon ramp state:
        public int CurrentTargetId = -1;
        public float RampTime;

        private readonly TowerDef _def;
        private readonly bool _adjacentPrism;

        public TowerInstance(TowerDef def, GridPos plot, bool adjacentPrism)
        {
            _def = def;
            DefId = def.Id;
            Plot = plot;
            Tier = 0;
            TotalInvested = def.Tiers[0].Cost;
            _adjacentPrism = adjacentPrism;
        }

        public bool IsDisabled => DisabledTimer > 0f;
        public int MaxTier => _def.Tiers.Length - 1;
        public bool IsMaxTier => Tier >= MaxTier && BranchId != null;
        public bool NeedsBranchChoice => Tier >= MaxTier && BranchId == null;

        /// <summary>Cost to upgrade to the next tier, or -1 if at max / awaiting branch.</summary>
        public int NextUpgradeCost
        {
            get
            {
                if (Tier < MaxTier) return _def.Tiers[Tier + 1].Cost;
                return -1; // at tier 3; use BranchCost
            }
        }

        /// <summary>Cost to pick a tier-3 branch capstone.</summary>
        public int BranchCost(bool branchA)
        {
            var b = branchA ? _def.BranchA : _def.BranchB;
            return b?.Cost ?? -1;
        }

        public bool TryUpgrade(Economy eco)
        {
            if (Tier >= MaxTier) return false;
            int cost = _def.Tiers[Tier + 1].Cost;
            if (!eco.TrySpend(cost)) return false;
            Tier++;
            TotalInvested += cost;
            return true;
        }

        public bool TryPickBranch(bool branchA, Economy eco)
        {
            if (Tier < MaxTier || BranchId != null) return false;
            var b = branchA ? _def.BranchA : _def.BranchB;
            if (b == null) return false;
            if (!eco.TrySpend(b.Cost)) return false;
            BranchId = b.Id;
            TotalInvested += b.Cost;
            return true;
        }

        /// <summary>Resolved stats after tier + branch + adjacency resonance.</summary>
        public TowerTierStats ResolveStats()
        {
            var baseStats = _def.Tiers[Tier];
            var s = new TowerTierStats
            {
                Damage = baseStats.Damage,
                Range = baseStats.Range,
                FireRate = baseStats.FireRate,
                IlluminationRadius = baseStats.IlluminationRadius,
                SlowPct = baseStats.SlowPct,
                ArmorShred = baseStats.ArmorShred,
                ChainArcs = baseStats.ChainArcs,
                Pierce = baseStats.Pierce,
                Cost = baseStats.Cost,
            };

            // Prism resonance: +1 arc per adjacent Prism.
            if (_def.Id == TowerIds.PrismArray && _adjacentPrism)
                s.ChainArcs += 1;

            if (BranchId != null)
            {
                BranchDef b = BranchId == _def.BranchA?.Id ? _def.BranchA : _def.BranchB;
                if (b != null)
                {
                    s.Damage *= b.DamageMult;
                    s.Range *= b.RangeMult;
                    s.FireRate *= b.FireRateMult;
                    s.IlluminationRadius *= b.IlluminationMult;
                    s.SlowPct = Clamp01(s.SlowPct + b.SlowPctDelta);
                    s.ArmorShred += b.ArmorShredDelta;
                    s.ChainArcs = System.Math.Max(0, s.ChainArcs + b.ChainArcsDelta);
                    s.Pierce = System.Math.Max(0, s.Pierce + b.PierceDelta);
                }
            }
            return s;
        }

        public BranchDef ActiveBranch()
        {
            if (BranchId == null) return null;
            return BranchId == _def.BranchA?.Id ? _def.BranchA : _def.BranchB;
        }

        private static float Clamp01(float v) => v < 0f ? 0f : (v > 0.9f ? 0.9f : v);

        /// <summary>Tick disable timer; returns true when the disable expires this tick.</summary>
        public bool TickDisabled(float dt)
        {
            if (DisabledTimer <= 0f) return false;
            DisabledTimer -= dt;
            if (DisabledTimer <= 0f) { DisabledTimer = 0f; return true; }
            return false;
        }
    }
}
