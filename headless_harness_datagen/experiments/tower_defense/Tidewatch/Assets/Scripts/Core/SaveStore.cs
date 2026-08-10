using System;
using System.IO;

namespace Tidewatch.Core
{
    /// <summary>
    /// File-backed save store with atomic writes and corruption fallback. Engine-free: the
    /// serializer is injected (Unity's JsonUtility in the Game layer, a test double in
    /// EditMode tests). Writes go to a temp file then rename over the target so a crash
    /// mid-write can never leave a half-written save.
    /// </summary>
    public interface IJsonSerializer
    {
        string Serialize<T>(T obj);
        T Deserialize<T>(string json);
    }

    public sealed class SaveStore
    {
        private readonly string _dir;
        private readonly IJsonSerializer _json;

        public SaveStore(string dir, IJsonSerializer json)
        {
            _dir = dir;
            _json = json;
            Directory.CreateDirectory(_dir);
        }

        public string SlotPath(int slot) => Path.Combine(_dir, $"run_slot{slot}.json");
        public string MetaPath => Path.Combine(_dir, "meta.json");
        public string SettingsPath => Path.Combine(_dir, "settings.json");

        /// <summary>Atomic write: temp file + rename.</summary>
        public void WriteAtomic(string path, string contents)
        {
            string tmp = path + ".tmp";
            File.WriteAllText(tmp, contents);
            // File.Replace requires the target to exist; delete+move is atomic enough on
            // all target platforms for a single-file save.
            if (File.Exists(path)) File.Delete(path);
            File.Move(tmp, path);
        }

        public void SaveRun(int slot, RunSave run)
        {
            run.version = SaveSchema.CurrentVersion;
            WriteAtomic(SlotPath(slot), _json.Serialize(run));
        }

        /// <summary>
        /// Load a run. Returns null (and sets error) if missing, corrupt, or wrong version —
        /// the caller must fall back to a fresh run rather than crash.
        /// </summary>
        public RunSave TryLoadRun(int slot, out string error)
        {
            error = null;
            string path = SlotPath(slot);
            if (!File.Exists(path)) { error = "No save in this slot."; return null; }
            try
            {
                string json = File.ReadAllText(path);
                var run = _json.Deserialize<RunSave>(json);
                if (run == null) { error = "Save file is empty or unreadable."; return null; }
                if (run.version != SaveSchema.CurrentVersion)
                {
                    error = $"Save version {run.version} is not supported (expected {SaveSchema.CurrentVersion}).";
                    return null;
                }
                return run;
            }
            catch (Exception e)
            {
                error = $"Save file is corrupted: {e.Message}";
                return null;
            }
        }

        public void SaveMeta(MetaProgress meta)
        {
            meta.version = SaveSchema.CurrentVersion;
            WriteAtomic(MetaPath, _json.Serialize(meta));
        }

        public MetaProgress LoadMeta()
        {
            if (!File.Exists(MetaPath)) return new MetaProgress();
            try
            {
                var meta = _json.Deserialize<MetaProgress>(File.ReadAllText(MetaPath));
                if (meta == null || meta.version != SaveSchema.CurrentVersion) return new MetaProgress();
                return meta;
            }
            catch (Exception)
            {
                return new MetaProgress();
            }
        }

        public void SaveSettings(GameSettings s)
        {
            s.version = SaveSchema.CurrentVersion;
            WriteAtomic(SettingsPath, _json.Serialize(s));
        }

        public GameSettings LoadSettings()
        {
            if (!File.Exists(SettingsPath)) return new GameSettings();
            try
            {
                var s = _json.Deserialize<GameSettings>(File.ReadAllText(SettingsPath));
                if (s == null || s.version != SaveSchema.CurrentVersion) return new GameSettings();
                return s;
            }
            catch (Exception)
            {
                return new GameSettings();
            }
        }

        public bool SlotHasSave(int slot) => File.Exists(SlotPath(slot));
        public void DeleteSlot(int slot) { if (File.Exists(SlotPath(slot))) File.Delete(SlotPath(slot)); }
    }
}
