using System.Collections.Generic;
using Tidewatch.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Tidewatch.Game
{
    /// <summary>
    /// Builds and switches all full-screen UI: main menu, level select, settings, briefing,
    /// pause, victory, defeat, endless results. All screens are styled via the Ui helpers.
    /// </summary>
    public sealed class ScreenManager : MonoBehaviour
    {
        private GameBootstrap _boot;
        private RunController _run;
        private AudioManager _audio;
        private HudController _hud;

        private RectTransform _root;
        private readonly List<GameObject> _openScreens = new List<GameObject>();
        private string _pendingLevelId;
        private string _pendingDifficultyId = DifficultyIds.RisingGale;
        private bool _pendingEndless;

        public void Init(GameBootstrap boot, RunController run, AudioManager audio)
        {
            _boot = boot;
            _run = run;
            _audio = audio;
            _root = (RectTransform)transform;
            _run.OnRunEnded += HandleRunEnded;
        }

        private void HandleRunEnded(bool victory)
        {
            if (_hud != null) _hud.gameObject.SetActive(false);
            if (victory) ShowVictory();
            else ShowDefeat();
        }

        public void AttachHud(HudController hud) => _hud = hud;

        private void CloseAll()
        {
            foreach (var s in _openScreens) if (s != null) Destroy(s);
            _openScreens.Clear();
        }

        private GameObject OpenPanel(string name)
        {
            CloseAll();
            var go = Ui.Panel(_root, name).gameObject;
            _openScreens.Add(go);
            return go;
        }

        // ------------------------------------------------------------------
        // Main menu
        // ------------------------------------------------------------------

        public void ShowMainMenu()
        {
            _run.AbandonRun();
            if (_hud != null) _hud.gameObject.SetActive(false);
            var p = OpenPanel("MainMenu");
            Ui.Label(p.transform, "Title", "TIDEWATCH", 84).rectTransform
                .Anchored(new Vector2(0.5f, 0.78f), new Vector2(700, 110));
            Ui.Label(p.transform, "Sub", "Lantern of the Shattered Coast", 30).rectTransform
                .Anchored(new Vector2(0.5f, 0.70f), new Vector2(700, 40));

            MakeMenuButton(p.transform, "Play", new Vector2(0.5f, 0.52f), () => { _audio.PlayUi(); ShowLevelSelect(); });
            MakeMenuButton(p.transform, "Load Run", new Vector2(0.5f, 0.42f), () => { _audio.PlayUi(); ShowLoadSlots(); });
            MakeMenuButton(p.transform, "Settings", new Vector2(0.5f, 0.32f), () => { _audio.PlayUi(); ShowSettings(); });
            MakeMenuButton(p.transform, "Quit", new Vector2(0.5f, 0.22f), () =>
            {
                _audio.PlayUi();
#if UNITY_EDITOR
                UnityEditor.EditorApplication.isPlaying = false;
#else
                Application.Quit();
#endif
            });
        }

        private void MakeMenuButton(Transform parent, string label, Vector2 center, System.Action onClick)
        {
            var b = Ui.Button(parent, label, label, onClick);
            b.GetComponent<RectTransform>().Anchored(center, new Vector2(340, 64));
        }

        // ------------------------------------------------------------------
        // Level select
        // ------------------------------------------------------------------

        public void ShowLevelSelect()
        {
            var p = OpenPanel("LevelSelect");
            Ui.Label(p.transform, "Title", "Select a Night", 44).rectTransform
                .Anchored(new Vector2(0.5f, 0.90f), new Vector2(600, 60));

            float y = 0.78f;
            foreach (var level in _boot.Levels)
            {
                bool unlocked = _boot.Meta.IsUnlocked(level.Id);
                var btn = Ui.Button(p.transform, level.Id, LevelButtonText(level, unlocked),
                    unlocked ? (System.Action)(() => { _audio.PlayUi(); ShowBriefing(level.Id); }) : null,
                    unlocked ? Ui.PanelBgLight : new Color(0.1f, 0.1f, 0.12f, 0.9f));
                btn.interactable = unlocked;
                btn.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, y), new Vector2(760, 78));
                y -= 0.11f;
            }
            BackButton(p.transform, ShowMainMenu);
        }

        private string LevelButtonText(LevelData level, bool unlocked)
        {
            if (!unlocked) return $"🔒  {level.DisplayName}";
            var sb = new System.Text.StringBuilder(level.DisplayName);
            foreach (var d in _boot.Db.Difficulties)
            {
                var rec = _boot.Meta.records.Find(r => r.levelId == level.Id && r.difficultyId == d.Id);
                if (rec != null && rec.cleared) sb.Append($"   ★{Abbrev(d.Id)}");
            }
            return sb.ToString();
        }

        private static string Abbrev(string diffId)
        {
            switch (diffId)
            {
                case DifficultyIds.CalmSea: return "C";
                case DifficultyIds.RisingGale: return "R";
                case DifficultyIds.AbyssalNight: return "A";
                default: return "?";
            }
        }

        // ------------------------------------------------------------------
        // Briefing (difficulty + mode)
        // ------------------------------------------------------------------

        public void ShowBriefing(string levelId)
        {
            _pendingLevelId = levelId;
            var level = _boot.GetLevel(levelId);
            var p = OpenPanel("Briefing");
            Ui.Label(p.transform, "Title", level.DisplayName, 46).rectTransform
                .Anchored(new Vector2(0.5f, 0.90f), new Vector2(800, 60));
            var brief = Ui.Label(p.transform, "Brief", level.Briefing, 24, TextAnchor.UpperCenter);
            brief.rectTransform.Anchored(new Vector2(0.5f, 0.74f), new Vector2(1100, 120));
            brief.horizontalOverflow = HorizontalWrapMode.Wrap;
            brief.verticalOverflow = VerticalWrapMode.Overflow;

            var enemies = Ui.Label(p.transform, "Enemies",
                "Expected: " + string.Join(", ", PrettyEnemies(level)), 22);
            enemies.rectTransform.Anchored(new Vector2(0.5f, 0.64f), new Vector2(1000, 40));

            // Tide hint.
            Ui.Label(p.transform, "Tide", TideHint(level), 20).rectTransform
                .Anchored(new Vector2(0.5f, 0.59f), new Vector2(1000, 40));

            // Difficulty buttons.
            float x = 0.28f;
            foreach (var d in _boot.Db.Difficulties)
            {
                string id = d.Id;
                var b = Ui.Button(p.transform, id, d.DisplayName, () =>
                {
                    _pendingDifficultyId = id;
                    _audio.PlayUi();
                    RefreshDifficultySelection(p);
                });
                b.GetComponent<RectTransform>().Anchored(new Vector2(x, 0.48f), new Vector2(300, 60));
                b.name = "diff_" + id;
                x += 0.22f;
            }

            // Mode: campaign or endless (endless only if level cleared).
            bool cleared = _boot.Meta.records.Exists(r => r.levelId == levelId && r.cleared);
            var campaignBtn = Ui.Button(p.transform, "mode_campaign", "Campaign Night", () =>
            { _pendingEndless = false; _audio.PlayUi(); RefreshModeSelection(p); });
            campaignBtn.GetComponent<RectTransform>().Anchored(new Vector2(0.36f, 0.38f), new Vector2(320, 60));
            campaignBtn.name = "mode_campaign";
            var endlessBtn = Ui.Button(p.transform, "mode_endless",
                cleared ? "Endless Night" : "Endless Night (clear level first)", () =>
            { if (cleared) { _pendingEndless = true; _audio.PlayUi(); RefreshModeSelection(p); } });
            endlessBtn.GetComponent<RectTransform>().Anchored(new Vector2(0.64f, 0.38f), new Vector2(360, 60));
            endlessBtn.name = "mode_endless";
            endlessBtn.interactable = cleared;

            var start = Ui.Button(p.transform, "Start", "Light the Lantern", () =>
            {
                _audio.PlayUi();
                StartPending();
            }, Ui.Accent * 0.6f);
            start.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, 0.24f), new Vector2(400, 74));

            BackButton(p.transform, ShowLevelSelect);
            RefreshDifficultySelection(p);
            RefreshModeSelection(p);
        }

        private IEnumerable<string> PrettyEnemies(LevelData level)
        {
            foreach (var id in level.ExpectedEnemies)
            {
                if (_boot.Db.TryGetEnemy(id, out var def)) yield return def.DisplayName;
            }
        }

        private static string TideHint(LevelData level)
        {
            var sb = new System.Text.StringBuilder("Tide: ");
            for (int i = 0; i < level.TideSchedule.Count; i++)
            {
                var t = level.TideSchedule[i];
                if (i > 0) sb.Append(" → ");
                sb.Append($"{t.Phase} {t.Seconds:0}s");
            }
            return sb.ToString();
        }

        private void RefreshDifficultySelection(GameObject panel)
        {
            foreach (var d in _boot.Db.Difficulties)
            {
                var t = panel.transform.Find("diff_" + d.Id);
                if (t != null)
                {
                    var img = t.GetComponent<Image>();
                    img.color = d.Id == _pendingDifficultyId ? Ui.Accent * 0.7f : Ui.PanelBgLight;
                }
            }
        }

        private void RefreshModeSelection(GameObject panel)
        {
            var c = panel.transform.Find("mode_campaign");
            var e = panel.transform.Find("mode_endless");
            if (c != null) c.GetComponent<Image>().color = !_pendingEndless ? Ui.Accent * 0.7f : Ui.PanelBgLight;
            if (e != null) e.GetComponent<Image>().color = _pendingEndless ? Ui.Accent * 0.7f : Ui.PanelBgLight;
        }

        private void StartPending()
        {
            var level = _boot.GetLevel(_pendingLevelId);
            if (level == null) return;
            if (!_boot.Db.TryGetDifficulty(_pendingDifficultyId, out var diff)) return;
            _run.AbandonRun();
            CloseAll();
            _hud.gameObject.SetActive(true);
            _run.StartRun(level, diff, _pendingEndless);
            _hud.OnRunStarted();
        }

        // ------------------------------------------------------------------
        // Save slots (load)
        // ------------------------------------------------------------------

        public void ShowLoadSlots()
        {
            var p = OpenPanel("LoadSlots");
            Ui.Label(p.transform, "Title", "Resume a Run", 44).rectTransform
                .Anchored(new Vector2(0.5f, 0.85f), new Vector2(600, 60));
            for (int slot = 0; slot < 3; slot++)
            {
                int s = slot;
                bool has = _boot.Saves.SlotHasSave(s);
                string label = has ? SlotLabel(s) : $"Slot {s + 1}  —  empty";
                var b = Ui.Button(p.transform, $"slot{s}", label,
                    has ? (System.Action)(() => { _audio.PlayUi(); LoadSlot(s); }) : null);
                b.interactable = has;
                b.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, 0.68f - s * 0.12f), new Vector2(640, 70));
            }
            BackButton(p.transform, ShowMainMenu);
        }

        private string SlotLabel(int slot)
        {
            var save = _boot.Saves.TryLoadRun(slot, out var err);
            if (save == null) return $"Slot {slot + 1}  —  corrupted";
            var level = _boot.GetLevel(save.levelId);
            string lname = level != null ? level.DisplayName : save.levelId;
            return $"Slot {slot + 1}  —  {lname}  ·  Wave {save.waveIndex}  ·  {save.salvage} Salvage";
        }

        private void LoadSlot(int slot)
        {
            var save = _boot.Saves.TryLoadRun(slot, out var err);
            if (save == null)
            {
                Debug.LogWarning($"[Tidewatch] Could not load slot {slot}: {err}");
                return;
            }
            var level = _boot.GetLevel(save.levelId);
            if (level == null || !_boot.Db.TryGetDifficulty(save.difficultyId, out var diff)) return;
            _run.AbandonRun();
            CloseAll();
            _hud.gameObject.SetActive(true);
            _run.ResumeFromSave(save, level, diff);
            _hud.OnRunStarted();
        }

        // ------------------------------------------------------------------
        // Settings
        // ------------------------------------------------------------------

        public void ShowSettings()
        {
            var p = OpenPanel("Settings");
            var s = _boot.Settings;
            Ui.Label(p.transform, "Title", "Settings", 44).rectTransform
                .Anchored(new Vector2(0.5f, 0.90f), new Vector2(600, 60));

            AddSlider(p.transform, "Master Volume", s.masterVolume, new Vector2(0.5f, 0.76f), v =>
            { s.masterVolume = v; _audio.ApplySettings(); });
            AddSlider(p.transform, "Music Volume", s.musicVolume, new Vector2(0.5f, 0.68f), v =>
            { s.musicVolume = v; _audio.ApplySettings(); });
            AddSlider(p.transform, "SFX Volume", s.sfxVolume, new Vector2(0.5f, 0.60f), v =>
            { s.sfxVolume = v; _audio.ApplySettings(); });

            AddToggle(p.transform, "Mute", s.muted, new Vector2(0.5f, 0.50f), v =>
            { s.muted = v; _audio.ApplySettings(); });
            AddToggle(p.transform, "Screen Shake", s.screenShake, new Vector2(0.5f, 0.43f), v => s.screenShake = v);
            AddToggle(p.transform, "Damage Numbers", s.damageNumbers, new Vector2(0.5f, 0.36f), v => s.damageNumbers = v);

            var back = Ui.Button(p.transform, "Back", "Back", () =>
            {
                _boot.PersistSettings();
                _audio.PlayUi();
                ShowMainMenu();
            });
            back.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, 0.22f), new Vector2(300, 60));
        }

        private void AddSlider(Transform parent, string label, float value, Vector2 center, System.Action<float> onChange)
        {
            Ui.Label(parent, label + "_lbl", label, 22).rectTransform
                .Anchored(center + new Vector2(0, 0.03f), new Vector2(400, 30));
            var sl = Ui.Slider(parent, label, value, v => { onChange(v); });
            sl.GetComponent<RectTransform>().Anchored(center + new Vector2(0, -0.015f), new Vector2(400, 24));
        }

        private void AddToggle(Transform parent, string label, bool value, Vector2 center, System.Action<bool> onChange)
        {
            var t = Ui.Toggle(parent, label, value, label, v => { onChange(v); _audio.PlayUi(); });
            t.GetComponent<RectTransform>().Anchored(center, new Vector2(320, 36));
        }

        // ------------------------------------------------------------------
        // Pause / victory / defeat
        // ------------------------------------------------------------------

        public void ShowPause()
        {
            var p = OpenPanel("Pause");
            Ui.Label(p.transform, "Title", "Paused", 54).rectTransform
                .Anchored(new Vector2(0.5f, 0.75f), new Vector2(400, 70));
            MakeMenuButton(p.transform, "Resume", new Vector2(0.5f, 0.58f), () =>
            { _audio.PlayUi(); Resume(); });
            MakeMenuButton(p.transform, "Save Run", new Vector2(0.5f, 0.48f), () =>
            { _audio.PlayUi(); ShowSaveSlots(); });
            MakeMenuButton(p.transform, "Settings", new Vector2(0.5f, 0.38f), () =>
            { _audio.PlayUi(); ShowSettingsFromPause(); });
            MakeMenuButton(p.transform, "Abandon Night", new Vector2(0.5f, 0.28f), () =>
            { _audio.PlayUi(); _run.SetPaused(false); ShowMainMenu(); });
        }

        private void ShowSettingsFromPause()
        {
            // Reuse settings screen; "Back" returns to pause.
            ShowSettings();
            var panel = _openScreens[_openScreens.Count - 1];
            var backBtn = panel.transform.Find("Back");
            if (backBtn != null)
            {
                var btn = backBtn.GetComponent<Button>();
                btn.onClick.RemoveAllListeners();
                btn.onClick.AddListener(() =>
                {
                    _boot.PersistSettings();
                    _audio.PlayUi();
                    ShowPause();
                });
            }
        }

        public void ShowSaveSlots()
        {
            var p = OpenPanel("SaveSlots");
            Ui.Label(p.transform, "Title", "Save Run (at wave boundary)", 40).rectTransform
                .Anchored(new Vector2(0.5f, 0.85f), new Vector2(700, 60));
            for (int slot = 0; slot < 3; slot++)
            {
                int s = slot;
                string label = _boot.Saves.SlotHasSave(s) ? SlotLabel(s) : $"Slot {s + 1}  —  empty";
                var b = Ui.Button(p.transform, $"slot{s}", label, () =>
                {
                    _run.SaveNow(s);
                    _audio.PlayUi();
                    Resume();
                });
                b.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, 0.68f - s * 0.12f), new Vector2(640, 70));
            }
            var cancel = Ui.Button(p.transform, "Cancel", "Cancel", () => { _audio.PlayUi(); ShowPause(); });
            cancel.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, 0.22f), new Vector2(300, 60));
        }

        public void Resume()
        {
            CloseAll();
            _run.SetPaused(false);
        }

        public void ShowVictory()
        {
            var sim = _run.Sim;
            var p = OpenPanel("Victory");
            Ui.Label(p.transform, "Title", "The Lantern Holds", 60).rectTransform
                .Anchored(new Vector2(0.5f, 0.78f), new Vector2(800, 80));
            Ui.Label(p.transform, "Stats", RunStats(sim), 26).rectTransform
                .Anchored(new Vector2(0.5f, 0.55f), new Vector2(700, 200));
            MakeMenuButton(p.transform, "Next Night", new Vector2(0.5f, 0.36f), () =>
            { _audio.PlayUi(); ShowLevelSelect(); });
            MakeMenuButton(p.transform, "Level Select", new Vector2(0.5f, 0.27f), () =>
            { _audio.PlayUi(); ShowLevelSelect(); });
        }

        public void ShowDefeat()
        {
            var sim = _run.Sim;
            var p = OpenPanel("Defeat");
            Ui.Label(p.transform, "Title", "The Light Has Gone Out", 52).rectTransform
                .Anchored(new Vector2(0.5f, 0.78f), new Vector2(900, 70));
            Ui.Label(p.transform, "Stats",
                $"Reached wave {sim.NextWaveIndex} of {sim.WaveCount}\n\n" + RunStats(sim), 26).rectTransform
                .Anchored(new Vector2(0.5f, 0.55f), new Vector2(700, 220));
            MakeMenuButton(p.transform, "Retry", new Vector2(0.5f, 0.34f), () =>
            {
                _audio.PlayUi();
                var level = _run.Level;
                var diff = _run.Difficulty;
                bool endless = _run.CurrentEndless;
                CloseAll();
                _run.AbandonRun();
                _run.StartRun(level, diff, endless);
            });
            MakeMenuButton(p.transform, "Level Select", new Vector2(0.5f, 0.25f), () =>
            { _audio.PlayUi(); ShowLevelSelect(); });
        }

        private static string RunStats(GameSim sim)
        {
            if (sim == null) return "";
            int mins = (int)(sim.Elapsed / 60f);
            int secs = (int)(sim.Elapsed % 60f);
            return $"Leaks: {sim.Leaks}\nSalvage earned: {sim.SalvageEarned}\n" +
                   $"Towers built: {sim.TowersBuilt}\nTime: {mins:00}:{secs:00}";
        }

        private void BackButton(Transform parent, System.Action onClick)
        {
            var b = Ui.Button(parent, "Back", "Back", () => { _audio.PlayUi(); onClick(); });
            b.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, 0.08f), new Vector2(280, 56));
        }
    }
}
