namespace Tidewatch.Core
{
    /// <summary>
    /// Deterministic RNG (xorshift128+) injected into all gameplay logic.
    /// No bare UnityEngine.Random is allowed in gameplay code; runs are
    /// reproducible from a run seed.
    /// </summary>
    public sealed class SeededRng
    {
        private ulong _s0;
        private ulong _s1;

        public SeededRng(ulong seed)
        {
            // Avoid the degenerate all-zero state.
            if (seed == 0) seed = 0x9E3779B97F4A7C15UL;
            _s0 = seed;
            _s1 = seed ^ 0x9E3779B97F4A7C15UL;
            // Warm up.
            for (int i = 0; i < 16; i++) NextUInt();
        }

        public ulong NextUInt()
        {
            ulong x = _s0;
            ulong y = _s1;
            _s0 = y;
            x ^= x << 23;
            _s1 = x ^ y ^ (x >> 17) ^ (y >> 26);
            return _s1 + y;
        }

        /// <summary>Inclusive-exclusive int range [min, max).</summary>
        public int Range(int min, int max)
        {
            if (max <= min) return min;
            return min + (int)(NextUInt() % (ulong)(max - min));
        }

        /// <summary>Float in [0, 1).</summary>
        public float NextFloat()
        {
            return (NextUInt() >> 11) * (1.0f / 9007199254740992.0f);
        }

        /// <summary>Float in [min, max).</summary>
        public float Range(float min, float max) => min + NextFloat() * (max - min);

        /// <summary>True with probability p (0..1).</summary>
        public bool Chance(float p) => NextFloat() < p;

        /// <summary>Serialize current state so a save can resume deterministically.</summary>
        public (ulong s0, ulong s1) GetState() => (_s0, _s1);

        public static SeededRng FromState(ulong s0, ulong s1)
        {
            var rng = new SeededRng(1);
            rng._s0 = s0;
            rng._s1 = s1;
            return rng;
        }
    }
}
