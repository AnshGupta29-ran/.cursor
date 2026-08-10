using System;
using System.Collections.Generic;

namespace Tidewatch.Core
{
    /// <summary>
    /// Save schema, version 1. Wave-boundary saves only (see README): a run is saved at the
    /// moment a wave is cleared. Mid-wave full-state serialization is the sanctioned
    /// simplification and is documented as a known limitation.
    ///
    /// Versioning policy: every save carries SaveVersion. The loader accepts only the
    /// current version; mismatched or unparseable files are reported and the caller falls
    /// back to a fresh run. The sim layer is engine-free, so DTOs use only primitives and
    /// System types and serialize with any JSON serializer (Unity JsonUtility in Game).
    /// </summary>
    public static class SaveSchema
    {
        public const int CurrentVersion = 1;
    }

    [Serializable]
    public sealed class TowerSave
    {
        public string defId;
        public int x;
        public int y;
        public int tier;
        public string branchId;
        public int priority;
        public int totalInvested;
        public float disabledTimer;
    }

    [Serializable]
    public sealed class RunSave
    {
        public int version = SaveSchema.CurrentVersion;
        public ulong runSeed;
        public ulong rngS0;
        public ulong rngS1;
        public string levelId;
        public string difficultyId;
        public int waveIndex;          // next wave to call (0-based); == waveCount => level done
        public int tideIndex;
        public float tideClock;
        public int salvage;
        public int lanternLight;
        public bool endless;
        public List<TowerSave> towers = new List<TowerSave>();
        // Records-relevant stats:
        public int leaks;
        public int salvageEarned;
        public int towersBuilt;
        public float elapsed;
    }

    /// <summary>Best clear for one (level, difficulty) pair.</summary>
    [Serializable]
    public sealed class LevelRecord
    {
        public string levelId;
        public string difficultyId;
        public bool cleared;
        public int bestWaveReached;
        public float bestTimeSeconds;
    }

    [Serializable]
    public sealed class MetaProgress
    {
        public int version = SaveSchema.CurrentVersion;
        public List<string> unlockedLevels = new List<string>();
        public List<LevelRecord> records = new List<LevelRecord>();

        public bool IsUnlocked(string levelId) => unlockedLevels.Contains(levelId);

        public LevelRecord GetOrAddRecord(string levelId, string difficultyId)
        {
            foreach (var r in records)
                if (r.levelId == levelId && r.difficultyId == difficultyId) return r;
            var rec = new LevelRecord { levelId = levelId, difficultyId = difficultyId };
            records.Add(rec);
            return rec;
        }
    }

    [Serializable]
    public sealed class GameSettings
    {
        public int version = SaveSchema.CurrentVersion;
        public float masterVolume = 1f;
        public float musicVolume = 0.8f;
        public float sfxVolume = 1f;
        public bool muted = false;
        public bool screenShake = true;
        public bool damageNumbers = true;
        public int speedPreference = 1;   // 1 or 2
        public int qualityLevel = 2;
    }
}
