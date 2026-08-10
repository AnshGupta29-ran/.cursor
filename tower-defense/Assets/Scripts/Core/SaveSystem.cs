using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace TD.Core
{
    /// <summary>Everything persisted between sessions.</summary>
    [Serializable]
    public class ProfileSave
    {
        public int version = 1;
        public List<string> unlockedLevels = new List<string> { "level1" };
        public List<LevelResult> results = new List<LevelResult>();
        public RunSnapshot run; // null when no suspended run
        public SettingsData settings = new SettingsData();
    }

    [Serializable]
    public class LevelResult
    {
        public string levelId;
        public int difficulty;
        public int bestScore;
        public bool completed;
    }

    [Serializable]
    public class RunSnapshot
    {
        public string levelId;
        public int difficulty;
        public int gold;
        public int lives;
        public int waveIndex;
        public int wavesCompleted;
        public int score;
        public int kills;
        public int earned;
        public List<TowerSnapshot> towers = new List<TowerSnapshot>();
        public List<EnemySnapshot> enemies = new List<EnemySnapshot>();
    }

    [Serializable]
    public class TowerSnapshot
    {
        public string towerId;
        public int nodeIndex;
        public int level;
    }

    [Serializable]
    public class EnemySnapshot
    {
        public string enemyId;
        public int segment;
        public float progress;
        public float health;
        public float slowRemaining;
        public float slowAmount;
    }

    [Serializable]
    public class SettingsData
    {
        public float masterVolume = 0.8f;
        public float musicVolume = 0.6f;
        public float sfxVolume = 0.9f;
        public int lastDifficulty = 1;
        public bool showRangeRings = true;
    }

    public static class SaveSystem
    {
        static string PathFor(string file) =>
            System.IO.Path.Combine(Application.persistentDataPath, file);

        const string ProfileFile = "profile.json";
        static ProfileSave _profile;

        public static ProfileSave Profile
        {
            get
            {
                if (_profile == null) _profile = Load();
                return _profile;
            }
        }

        public static SettingsData Settings => Profile.settings;

        public static ProfileSave Load()
        {
            try
            {
                string path = PathFor(ProfileFile);
                if (File.Exists(path))
                {
                    var p = JsonUtility.FromJson<ProfileSave>(File.ReadAllText(path));
                    if (p != null) return p;
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"Save load failed, starting fresh: {e.Message}");
            }
            return new ProfileSave();
        }

        public static void Save()
        {
            try
            {
                File.WriteAllText(PathFor(ProfileFile), JsonUtility.ToJson(Profile, true));
            }
            catch (Exception e)
            {
                Debug.LogWarning($"Save failed: {e.Message}");
            }
        }

        // -- progress -------------------------------------------------------
        public static bool IsLevelUnlocked(string levelId) => Profile.unlockedLevels.Contains(levelId);

        public static void UnlockLevel(string levelId)
        {
            if (string.IsNullOrEmpty(levelId)) return;
            if (!Profile.unlockedLevels.Contains(levelId))
            {
                Profile.unlockedLevels.Add(levelId);
                Save();
            }
        }

        public static void RecordResult(string levelId, int difficulty, int score, bool completed)
        {
            var r = Profile.results.Find(x => x.levelId == levelId && x.difficulty == difficulty);
            if (r == null)
            {
                r = new LevelResult { levelId = levelId, difficulty = difficulty };
                Profile.results.Add(r);
            }
            r.bestScore = Mathf.Max(r.bestScore, score);
            r.completed |= completed;
            Save();
        }

        public static LevelResult GetResult(string levelId, int difficulty) =>
            Profile.results.Find(x => x.levelId == levelId && x.difficulty == difficulty);

        // -- suspended run --------------------------------------------------
        public static void SaveRun(RunSnapshot snap)
        {
            Profile.run = snap;
            Save();
        }

        public static void ClearRun()
        {
            Profile.run = null;
            Save();
        }

        public static bool HasSavedRun => Profile.run != null;

        public static void ResetAll()
        {
            _profile = new ProfileSave();
            Save();
        }
    }
}
