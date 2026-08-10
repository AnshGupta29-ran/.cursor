using System.Collections.Generic;
using System.Text;

namespace Tidewatch.Core
{
    /// <summary>One spawn group inside a wave.</summary>
    public struct SpawnEntry
    {
        public string EnemyId;
        public int Count;
        /// <summary>Seconds between individual spawns of this entry.</summary>
        public float Interval;
        /// <summary>Index into the level's gate list.</summary>
        public int GateIndex;
        /// <summary>Seconds after wave start before this entry begins spawning.</summary>
        public float Delay;

        public SpawnEntry(string enemyId, int count, float interval, int gateIndex, float delay)
        {
            EnemyId = enemyId; Count = count; Interval = interval; GateIndex = gateIndex; Delay = delay;
        }
    }

    /// <summary>A single wave: a list of spawn entries.</summary>
    public sealed class WaveDef
    {
        public List<SpawnEntry> Entries = new List<SpawnEntry>();
        /// <summary>Optional composition variance seed offset; combined with run seed.</summary>
        public int VarianceSeed;
    }

    /// <summary>Validation result for a wave list.</summary>
    public sealed class WaveValidation
    {
        public bool Ok => Errors.Count == 0;
        public readonly List<string> Errors = new List<string>();
        public void Error(string msg) => Errors.Add(msg);
        public override string ToString()
        {
            var sb = new StringBuilder();
            foreach (var e in Errors) sb.AppendLine(e);
            return sb.ToString();
        }
    }

    /// <summary>
    /// Wave list parsing + validation. Waves arrive as plain data (from JSON or built in
    /// code) and are validated against the ContentDb so bad enemy ids and zero counts are
    /// rejected before a run starts. Pure C# for EditMode tests.
    /// </summary>
    public static class WaveSystem
    {
        public static WaveValidation Validate(IReadOnlyList<WaveDef> waves, ContentDb db, int gateCount)
        {
            var v = new WaveValidation();
            if (waves == null || waves.Count == 0)
            {
                v.Error("Wave list is empty.");
                return v;
            }
            for (int i = 0; i < waves.Count; i++)
            {
                var w = waves[i];
                if (w.Entries.Count == 0) { v.Error($"Wave {i}: no spawn entries."); continue; }
                for (int j = 0; j < w.Entries.Count; j++)
                {
                    var e = w.Entries[j];
                    if (string.IsNullOrEmpty(e.EnemyId))
                        v.Error($"Wave {i} entry {j}: empty enemy id.");
                    else if (!db.HasEnemy(e.EnemyId))
                        v.Error($"Wave {i} entry {j}: unknown enemy id '{e.EnemyId}'.");
                    if (e.Count <= 0)
                        v.Error($"Wave {i} entry {j}: count must be > 0 (got {e.Count}).");
                    if (e.Interval < 0f)
                        v.Error($"Wave {i} entry {j}: interval must be >= 0 (got {e.Interval}).");
                    if (e.GateIndex < 0 || e.GateIndex >= gateCount)
                        v.Error($"Wave {i} entry {j}: gate index {e.GateIndex} out of range (0..{gateCount - 1}).");
                }
            }
            return v;
        }

        /// <summary>
        /// Expand a wave into an ordered spawn schedule of (time, enemyId, gateIndex),
        /// applying seeded composition variance so runs are reproducible from a run seed.
        /// </summary>
        public static List<(float time, string enemyId, int gate)> BuildSpawnSchedule(
            WaveDef wave, SeededRng rng)
        {
            var schedule = new List<(float, string, int)>();
            foreach (var e in wave.Entries)
            {
                int count = e.Count;
                // Optional variance: +/-10% count, deterministic from rng.
                if (wave.VarianceSeed != 0)
                {
                    float jitter = rng.Range(-0.1f, 0.1f);
                    count = System.Math.Max(1, (int)System.Math.Round(count * (1f + jitter)));
                }
                for (int k = 0; k < count; k++)
                {
                    float t = e.Delay + k * e.Interval;
                    schedule.Add((t, e.EnemyId, e.GateIndex));
                }
            }
            schedule.Sort((a, b) => a.Item1.CompareTo(b.Item1));
            return schedule;
        }

        /// <summary>Total enemies a wave will spawn (for HUD preview / wave-clear detection).</summary>
        public static int TotalCount(WaveDef wave)
        {
            int n = 0;
            foreach (var e in wave.Entries) n += e.Count;
            return n;
        }
    }
}
