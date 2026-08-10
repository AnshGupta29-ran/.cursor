using System.Collections.Generic;
using TD.Content;
using TD.Core;
using TD.Towers;
using UnityEngine;
using UnityEngine.UI;

namespace TD.UI
{
    /// <summary>
    /// All game UI built in code (no prefabs / no .unity layout edits needed).
    /// Main menu with level select + difficulty, in-game HUD, tower shop,
    /// selected-tower panel, pause menu, settings, win/lose screens.
    /// </summary>
    public class UIManager : MonoBehaviour
    {
        GameManager _gm;
        GameBootstrap _boot;
        Canvas _canvas;

        // panels
        GameObject _menuPanel, _hudPanel, _pausePanel, _settingsPanel, _endPanel, _levelSelectPanel;

        // HUD
        Text _goldText, _livesText, _waveText, _speedText, _scoreText;
        readonly List<Button> _shopButtons = new List<Button>();
        readonly List<Text> _shopCostLabels = new List<Text>();

        // selected tower panel
        GameObject _selPanel;
        Text _selTitle, _selStats, _upgradeLabel;
        Button _upgradeButton;

        // end screen
        Text _endTitle, _endStats;
        Button _nextLevelButton;

        // level select
        readonly List<Button> _levelButtons = new List<Button>();
        int _menuDifficulty = 1;
        Text[] _diffLabels;

        static readonly string[] DifficultyNames = { "Easy", "Normal", "Hard" };

        void Start()
        {
            _gm = GameManager.Instance;
            _boot = FindObjectOfType<GameBootstrap>();
            _menuDifficulty = SaveSystem.Settings.lastDifficulty;

            BuildCanvas();
            BuildMenuPanel();
            BuildLevelSelectPanel();
            BuildHud();
            BuildSelectedPanel();
            BuildPausePanel();
            BuildSettingsPanel();
            BuildEndPanel();

            _gm.StateChanged += Refresh;
            _gm.EconomyChanged += RefreshHud;
            _gm.LivesChanged += RefreshHud;
            _gm.WaveChanged += RefreshHud;
            if (BuildManager.Instance != null)
            {
                BuildManager.Instance.SelectionChanged += RefreshSelection;
                BuildManager.Instance.PlacementModeChanged += RefreshShop;
            }
            Refresh();
        }

        void OnDestroy()
        {
            if (_gm != null)
            {
                _gm.StateChanged -= Refresh;
                _gm.EconomyChanged -= RefreshHud;
                _gm.LivesChanged -= RefreshHud;
                _gm.WaveChanged -= RefreshHud;
            }
            if (BuildManager.Instance != null)
            {
                BuildManager.Instance.SelectionChanged -= RefreshSelection;
                BuildManager.Instance.PlacementModeChanged -= RefreshShop;
            }
        }

        // ==================================================================
        // Canvas + widget helpers
        // ==================================================================
        void BuildCanvas()
        {
            var go = new GameObject("Canvas");
            go.transform.SetParent(transform, false);
            _canvas = go.AddComponent<Canvas>();
            _canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = go.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            go.AddComponent<GraphicRaycaster>();
        }

        RectTransform Panel(string name, Transform parent, Color bg)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var rt = go.AddComponent<RectTransform>();
            var img = go.AddComponent<Image>();
            img.color = bg;
            return rt;
        }

        Text Label(Transform parent, string text, int size, TextAnchor anchor = TextAnchor.MiddleCenter)
        {
            var go = new GameObject("label");
            go.transform.SetParent(parent, false);
            go.AddComponent<RectTransform>();
            var t = go.AddComponent<Text>();
            t.font = DefaultFont;
            t.text = text;
            t.fontSize = size;
            t.alignment = anchor;
            t.color = Color.white;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            return t;
        }

        Button MakeButton(Transform parent, string label, int fontSize, UnityEngine.Events.UnityAction onClick)
        {
            var go = new GameObject("btn_" + label);
            go.transform.SetParent(parent, false);
            var rt = go.AddComponent<RectTransform>();
            rt.sizeDelta = new Vector2(340, 64);
            var img = go.AddComponent<Image>();
            img.color = new Color(0.22f, 0.30f, 0.42f);
            var btn = go.AddComponent<Button>();
            var colors = btn.colors;
            colors.highlightedColor = new Color(0.30f, 0.42f, 0.58f);
            colors.pressedColor = new Color(0.16f, 0.22f, 0.32f);
            colors.disabledColor = new Color(0.15f, 0.15f, 0.18f);
            btn.colors = colors;
            btn.onClick.AddListener(() => AudioManager.Instance?.Play(SfxId.UIClick));
            btn.onClick.AddListener(onClick);
            var t = Label(go.transform, label, fontSize);
            Stretch(t.rectTransform);
            return btn;
        }

        static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero; rt.offsetMax = Vector2.zero;
        }

        static void Place(RectTransform rt, float x, float y, float w, float h,
            TextAnchor anchor = TextAnchor.MiddleCenter)
        {
            var a = AnchorFor(anchor);
            rt.anchorMin = a; rt.anchorMax = a;
            rt.pivot = a;
            rt.anchoredPosition = new Vector2(x, y);
            rt.sizeDelta = new Vector2(w, h);
        }

        static Vector2 AnchorFor(TextAnchor a)
        {
            switch (a)
            {
                case TextAnchor.UpperLeft: return new Vector2(0, 1);
                case TextAnchor.UpperCenter: return new Vector2(0.5f, 1);
                case TextAnchor.UpperRight: return new Vector2(1, 1);
                case TextAnchor.MiddleLeft: return new Vector2(0, 0.5f);
                case TextAnchor.MiddleRight: return new Vector2(1, 0.5f);
                case TextAnchor.LowerLeft: return new Vector2(0, 0);
                case TextAnchor.LowerCenter: return new Vector2(0.5f, 0);
                case TextAnchor.LowerRight: return new Vector2(1, 0);
                default: return new Vector2(0.5f, 0.5f);
            }
        }

        // ==================================================================
        // Main menu
        // ==================================================================
        void BuildMenuPanel()
        {
            var rt = Panel("MenuPanel", _canvas.transform, new Color(0.07f, 0.09f, 0.14f, 0.92f));
            Stretch(rt);
            _menuPanel = rt.gameObject;

            var title = Label(rt, "CRYSTAL DEFENSE", 96);
            Place(title.rectTransform, 0, -160, 1200, 120, TextAnchor.UpperCenter);
            title.color = new Color(0.55f, 0.85f, 1f);

            var sub = Label(rt, "A tower defense", 30);
            Place(sub.rectTransform, 0, -250, 800, 40, TextAnchor.UpperCenter);
            sub.color = new Color(0.7f, 0.75f, 0.85f);

            var play = MakeButton(rt, "PLAY", 34, () => ShowOnly(_levelSelectPanel));
            Place((RectTransform)play.transform, 0, 80, 380, 76);

            var cont = MakeButton(rt, "CONTINUE RUN", 30, () => _boot.ResumeSavedRun());
            Place((RectTransform)cont.transform, 0, -16, 380, 70);
            cont.gameObject.SetActive(SaveSystem.HasSavedRun);
            _continueButton = cont;

            var settings = MakeButton(rt, "SETTINGS", 30, () => ShowOnly(_settingsPanel));
            Place((RectTransform)settings.transform, 0, -108, 380, 70);

            var quit = MakeButton(rt, "QUIT", 30, Application.Quit);
            Place((RectTransform)quit.transform, 0, -200, 380, 70);

            var hint = Label(rt, "WASD / edge-pan camera · scroll to zoom · Space pause · F speed · Enter next wave", 20);
            Place(hint.rectTransform, 0, 40, 1600, 30, TextAnchor.LowerCenter);
            hint.color = new Color(0.55f, 0.6f, 0.7f);
        }

        Button _continueButton;

        void BuildLevelSelectPanel()
        {
            var rt = Panel("LevelSelect", _canvas.transform, new Color(0.07f, 0.09f, 0.14f, 0.95f));
            Stretch(rt);
            _levelSelectPanel = rt.gameObject;

            var title = Label(rt, "SELECT LEVEL", 56);
            Place(title.rectTransform, 0, -110, 900, 80, TextAnchor.UpperCenter);

            // difficulty picker
            var diffTitle = Label(rt, "DIFFICULTY", 26);
            Place(diffTitle.rectTransform, 0, -210, 500, 36, TextAnchor.UpperCenter);
            diffTitle.color = new Color(0.7f, 0.75f, 0.85f);

            _diffLabels = new Text[3];
            for (int i = 0; i < 3; i++)
            {
                int d = i;
                var b = MakeButton(rt, DifficultyNames[i], 26, () => { _menuDifficulty = d; RefreshDifficultyButtons(); });
                Place((RectTransform)b.transform, (i - 1) * 240, -300, 220, 64, TextAnchor.UpperCenter);
                _diffLabels[i] = b.GetComponentInChildren<Text>();
                _diffButtons[i] = b;
            }
            RefreshDifficultyButtons();

            // one card per level
            _levelButtons.Clear();
            for (int i = 0; i < _gm.levelDefs.Count; i++)
            {
                var level = _gm.levelDefs[i];
                var card = Panel($"level_{level.id}", rt, new Color(0.13f, 0.17f, 0.25f));
                Place(card, (i - (_gm.levelDefs.Count - 1) / 2f) * 430, 40, 400, 380);

                var name = Label(card, level.displayName, 34);
                Place(name.rectTransform, 0, -50, 380, 50, TextAnchor.UpperCenter);

                var desc = Label(card, level.description, 20);
                Place(desc.rectTransform, 0, 20, 360, 140);
                desc.color = new Color(0.7f, 0.75f, 0.85f);

                var best = SaveSystem.GetResult(level.id, _menuDifficulty);
                var stat = Label(card, best != null && best.bestScore > 0 ? $"Best: {best.bestScore}" : "—", 22);
                stat.name = "best";
                Place(stat.rectTransform, 0, -140, 360, 30, TextAnchor.LowerCenter);
                stat.color = new Color(1f, 0.85f, 0.3f);

                bool unlocked = SaveSystem.IsLevelUnlocked(level.id);
                var b = MakeButton(card, unlocked ? "START" : "LOCKED", 26, () => _boot.BeginLevel(level.id, _menuDifficulty));
                Place((RectTransform)b.transform, 0, 50, 260, 64, TextAnchor.LowerCenter);
                b.interactable = unlocked;
                _levelButtons.Add(b);
            }

            var back = MakeButton(rt, "BACK", 26, () => ShowOnly(_menuPanel));
            Place((RectTransform)back.transform, -60, 60, 240, 60, TextAnchor.LowerLeft);
        }

        readonly Button[] _diffButtons = new Button[3];

        void RefreshDifficultyButtons()
        {
            for (int i = 0; i < 3; i++)
            {
                bool on = i == _menuDifficulty;
                var img = _diffButtons[i].GetComponent<Image>();
                img.color = on ? new Color(0.35f, 0.55f, 0.75f) : new Color(0.22f, 0.30f, 0.42f);
            }
            // refresh best-score labels per difficulty
            for (int i = 0; i < _levelButtons.Count; i++)
            {
                var level = _gm.levelDefs[i];
                var card = _levelButtons[i].transform.parent;
                var stat = card.Find("best")?.GetComponent<Text>();
                if (stat == null) continue;
                var best = SaveSystem.GetResult(level.id, _menuDifficulty);
                stat.text = best != null && best.bestScore > 0 ? $"Best: {best.bestScore}" : "—";
            }
        }

        // ==================================================================
        // HUD
        // ==================================================================
        void BuildHud()
        {
            var rt = Panel("HUD", _canvas.transform, new Color(0, 0, 0, 0));
            Stretch(rt);
            var img = rt.GetComponent<Image>();
            img.raycastTarget = false;
            _hudPanel = rt.gameObject;

            // top bar
            var bar = Panel("topbar", rt, new Color(0.07f, 0.09f, 0.14f, 0.85f));
            Place(bar, 0, 0, 1920, 64, TextAnchor.UpperCenter);
            var barImg = bar.GetComponent<Image>(); barImg.raycastTarget = false;

            _goldText = HudLabel(bar, -860, "💰 0");
            _livesText = HudLabel(bar, -600, "❤ 0");
            _waveText = HudLabel(bar, -300, "Wave 0/0");
            _scoreText = HudLabel(bar, 20, "Score 0");
            _speedText = HudLabel(bar, 420, "1×");

            var speedBtn = MakeButton(bar, "SPEED (F)", 20, () => _gm.CycleGameSpeed());
            Place((RectTransform)speedBtn.transform, 620, 0, 160, 48, TextAnchor.MiddleCenter);
            var pauseBtn = MakeButton(bar, "❚❚", 22, () => _gm.PauseGame());
            Place((RectTransform)pauseBtn.transform, 800, 0, 64, 48, TextAnchor.MiddleCenter);

            // wave call button (bottom center)
            var waveBtn = MakeButton(rt, "START WAVE (Enter)", 26,
                () => Enemies.WaveSpawner.Instance?.StartNextWave());
            Place((RectTransform)waveBtn.transform, 0, 60, 340, 64, TextAnchor.LowerCenter);
            _waveButton = waveBtn;

            // shop bar (right side)
            var shop = Panel("shop", rt, new Color(0.07f, 0.09f, 0.14f, 0.85f));
            Place(shop, -16, 0, 240, 560, TextAnchor.MiddleRight);
            _shopButtons.Clear();
            _shopCostLabels.Clear();
            for (int i = 0; i < _gm.towerDefs.Count; i++)
            {
                var def = _gm.towerDefs[i];
                var card = Panel($"shop_{def.id}", shop, new Color(0.13f, 0.17f, 0.25f));
                Place(card, 0, 200 - i * 135, 208, 120);

                var name = Label(card, def.displayName, 20);
                Place(name.rectTransform, 0, -14, 200, 26, TextAnchor.UpperCenter);

                var cost = Label(card, $"{def.BuildCost}g", 22);
                Place(cost.rectTransform, 0, -44, 200, 26, TextAnchor.UpperCenter);
                cost.color = new Color(1f, 0.85f, 0.3f);
                _shopCostLabels.Add(cost);

                var b = MakeButton(card, "BUILD", 20, () => BuildManager.Instance.BeginPlacement(def));
                Place((RectTransform)b.transform, 0, 18, 160, 48, TextAnchor.LowerCenter);
                _shopButtons.Add(b);
            }

            RefreshHud();
        }

        Button _waveButton;

        Text HudLabel(Transform parent, float x, string text)
        {
            var t = Label(parent, text, 26, TextAnchor.MiddleLeft);
            Place(t.rectTransform, x, 0, 260, 40, TextAnchor.MiddleCenter);
            t.rectTransform.anchoredPosition = new Vector2(x, 0);
            return t;
        }

        void RefreshHud()
        {
            if (_gm == null || _goldText == null) return;
            _goldText.text = $"💰 {_gm.Gold}";
            _livesText.text = $"❤ {_gm.Lives}";
            int total = _gm.CurrentLevel != null && _gm.CurrentLevel.waves != null
                ? _gm.CurrentLevel.waves.waves.Length : 0;
            _waveText.text = $"Wave {Mathf.Max(0, _gm.WaveIndex + 1)}/{total}";
            _scoreText.text = $"Score {_gm.Score}";
            _speedText.text = $"{_gm.GameSpeed}×";
            RefreshShop();
            if (_waveButton != null)
                _waveButton.interactable = _gm.State == GameState.Playing && !_gm.WaveInProgress
                    && _gm.WaveIndex + 1 < total;
        }

        void RefreshShop()
        {
            if (_gm == null) return;
            for (int i = 0; i < _shopButtons.Count && i < _gm.towerDefs.Count; i++)
            {
                bool afford = _gm.CanAfford(_gm.towerDefs[i].BuildCost);
                _shopButtons[i].interactable = afford;
                _shopCostLabels[i].color = afford ? new Color(1f, 0.85f, 0.3f) : new Color(0.6f, 0.3f, 0.3f);
            }
            RefreshHudWaveOnly();
        }

        void RefreshHudWaveOnly()
        {
            // wave button interactability already handled in RefreshHud
        }

        // ==================================================================
        // Selected tower panel (upgrade / sell)
        // ==================================================================
        void BuildSelectedPanel()
        {
            var rt = Panel("SelectedPanel", _canvas.transform, new Color(0.07f, 0.09f, 0.14f, 0.92f));
            Place(rt, 16, 0, 300, 420, TextAnchor.MiddleLeft);
            _selPanel = rt.gameObject;

            _selTitle = Label(rt, "Tower", 28);
            Place(_selTitle.rectTransform, 0, -40, 280, 36, TextAnchor.UpperCenter);

            _selStats = Label(rt, "", 19);
            Place(_selStats.rectTransform, 0, 40, 270, 160);
            _selStats.color = new Color(0.8f, 0.85f, 0.95f);

            _upgradeButton = MakeButton(rt, "UPGRADE", 24, () => BuildManager.Instance.TryUpgradeSelected());
            Place((RectTransform)_upgradeButton.transform, 0, -60, 240, 56, TextAnchor.LowerCenter);
            _upgradeLabel = _upgradeButton.GetComponentInChildren<Text>();

            var sell = MakeButton(rt, "SELL", 24, () => BuildManager.Instance.SellSelected());
            Place((RectTransform)sell.transform, 0, -140, 240, 56, TextAnchor.LowerCenter);
            sell.GetComponent<Image>().color = new Color(0.45f, 0.25f, 0.22f);

            _selPanel.SetActive(false);
        }

        void RefreshSelection()
        {
            var t = BuildManager.Instance != null ? BuildManager.Instance.Selected : null;
            if (t == null) { _selPanel.SetActive(false); return; }
            _selPanel.SetActive(true);
            var s = t.Def.levels[t.Level];
            _selTitle.text = $"{t.Def.displayName}  Lv{t.Level + 1}";
            _selStats.text =
                $"Damage   {s.damage:0.#}\n" +
                $"Range    {s.range:0.#}\n" +
                $"Rate     {s.fireRate:0.#}/s\n" +
                (s.splashRadius > 0f ? $"Splash   {s.splashRadius:0.#}\n" : "") +
                (s.slowAmount > 0f ? $"Slow     {s.slowAmount * 100f:0}% / {s.slowDuration:0.#}s\n" : "") +
                (s.armorPierce > 0f ? $"Pierce   {s.armorPierce * 100f:0}%\n" : "") +
                $"\n{t.Def.upgradeHint}";
            if (t.CanUpgrade)
            {
                _upgradeButton.interactable = _gm.CanAfford(t.NextUpgradeCost);
                _upgradeLabel.text = $"UPGRADE  {t.NextUpgradeCost}g";
            }
            else
            {
                _upgradeButton.interactable = false;
                _upgradeLabel.text = "MAX LEVEL";
            }
        }

        // ==================================================================
        // Pause menu
        // ==================================================================
        void BuildPausePanel()
        {
            var rt = Panel("PausePanel", _canvas.transform, new Color(0.05f, 0.06f, 0.10f, 0.85f));
            Stretch(rt);
            _pausePanel = rt.gameObject;

            var title = Label(rt, "PAUSED", 64);
            Place(title.rectTransform, 0, -140, 600, 90, TextAnchor.UpperCenter);

            var resume = MakeButton(rt, "RESUME", 30, () => _gm.ResumeGame());
            Place((RectTransform)resume.transform, 0, 110, 360, 70);

            var settings = MakeButton(rt, "SETTINGS", 28, () => ShowOnly(_settingsPanel));
            Place((RectTransform)settings.transform, 0, 20, 360, 64);

            var saveQuit = MakeButton(rt, "SAVE & QUIT", 28, () => _boot.SaveAndQuitToMenu());
            Place((RectTransform)saveQuit.transform, 0, -64, 360, 64);

            var abandon = MakeButton(rt, "ABANDON RUN", 28, () => _boot.AbandonRun());
            Place((RectTransform)abandon.transform, 0, -148, 360, 64);
            abandon.GetComponent<Image>().color = new Color(0.45f, 0.25f, 0.22f);
        }

        // ==================================================================
        // Settings
        // ==================================================================
        void BuildSettingsPanel()
        {
            var rt = Panel("SettingsPanel", _canvas.transform, new Color(0.07f, 0.09f, 0.14f, 0.95f));
            Stretch(rt);
            _settingsPanel = rt.gameObject;

            var title = Label(rt, "SETTINGS", 56);
            Place(title.rectTransform, 0, -120, 600, 80, TextAnchor.UpperCenter);

            BuildSlider(rt, "Master Volume", 0, v => SaveSystem.Settings.masterVolume = v,
                () => SaveSystem.Settings.masterVolume);
            BuildSlider(rt, "Music Volume", 1, v => SaveSystem.Settings.musicVolume = v,
                () => SaveSystem.Settings.musicVolume);
            BuildSlider(rt, "SFX Volume", 2, v => SaveSystem.Settings.sfxVolume = v,
                () => SaveSystem.Settings.sfxVolume);

            var back = MakeButton(rt, "BACK", 26, () =>
            {
                SaveSystem.Save();
                ShowOnly(_gm.State == GameState.Paused ? _pausePanel : _menuPanel);
            });
            Place((RectTransform)back.transform, 0, -140, 300, 64, TextAnchor.LowerCenter);
        }

        void BuildSlider(Transform parent, string label, int row,
            UnityEngine.Events.UnityAction<float> onChange, System.Func<float> getter)
        {
            var t = Label(parent, label, 26, TextAnchor.MiddleLeft);
            Place(t.rectTransform, -320, 120 - row * 90, 320, 40);

            var go = new GameObject("slider_" + label);
            go.transform.SetParent(parent, false);
            var srt = go.AddComponent<RectTransform>();
            Place(srt, 80, 120 - row * 90, 420, 30);
            var slider = go.AddComponent<Slider>();
            slider.minValue = 0f; slider.maxValue = 1f;

            var bg = Panel("bg", go.transform, new Color(0.15f, 0.15f, 0.20f));
            Stretch(bg);
            var fillArea = new GameObject("fill").AddComponent<RectTransform>();
            fillArea.transform.SetParent(go.transform, false);
            Stretch(fillArea);
            var fill = Panel("f", fillArea, new Color(0.40f, 0.65f, 0.90f));
            Stretch(fill);
            slider.fillRect = fill;
            slider.targetGraphic = bg.GetComponent<Image>();
            slider.value = getter();
            slider.onValueChanged.AddListener(v => onChange(v));
        }

        // ==================================================================
        // Win / lose screens
        // ==================================================================
        void BuildEndPanel()
        {
            var rt = Panel("EndPanel", _canvas.transform, new Color(0.05f, 0.06f, 0.10f, 0.88f));
            Stretch(rt);
            _endPanel = rt.gameObject;

            _endTitle = Label(rt, "VICTORY", 84);
            Place(_endTitle.rectTransform, 0, -170, 900, 110, TextAnchor.UpperCenter);

            _endStats = Label(rt, "", 30);
            Place(_endStats.rectTransform, 0, 40, 900, 200);
            _endStats.color = new Color(0.8f, 0.85f, 0.95f);

            _nextLevelButton = MakeButton(rt, "NEXT LEVEL", 30, () =>
            {
                var next = _gm.NextLevelId();
                if (next != null) _boot.BeginLevel(next, _gm.Difficulty);
            });
            Place((RectTransform)_nextLevelButton.transform, 0, -90, 360, 70);

            var retry = MakeButton(rt, "RETRY", 28, () => _boot.BeginLevel(_gm.CurrentLevel.id, _gm.Difficulty));
            Place((RectTransform)retry.transform, 0, -180, 360, 64);

            var menu = MakeButton(rt, "MAIN MENU", 28, () => _boot.AbandonRun());
            Place((RectTransform)menu.transform, 0, -264, 360, 64);
        }

        // ==================================================================
        // State routing
        // ==================================================================
        void Refresh()
        {
            switch (_gm.State)
            {
                case GameState.Menu:
                    ShowOnly(_menuPanel);
                    if (_continueButton != null)
                        _continueButton.gameObject.SetActive(SaveSystem.HasSavedRun);
                    break;
                case GameState.Playing:
                    ShowOnly(_hudPanel);
                    RefreshHud();
                    RefreshSelection();
                    break;
                case GameState.Paused:
                    ShowOnly(_pausePanel);
                    break;
                case GameState.Won:
                    SetupEnd(true);
                    ShowOnly(_endPanel);
                    AudioManager.Instance?.Play(SfxId.Victory);
                    break;
                case GameState.Lost:
                    SetupEnd(false);
                    ShowOnly(_endPanel);
                    AudioManager.Instance?.Play(SfxId.Defeat);
                    break;
            }
        }

        void SetupEnd(bool won)
        {
            _endTitle.text = won ? "VICTORY!" : "BASE OVERRUN";
            _endTitle.color = won ? new Color(0.5f, 1f, 0.6f) : new Color(1f, 0.4f, 0.35f);
            _endStats.text =
                $"Level: {_gm.CurrentLevel.displayName}  ({DifficultyNames[_gm.Difficulty]})\n" +
                $"Score: {_gm.Score}\n" +
                $"Waves cleared: {_gm.WavesCompleted}\n" +
                $"Enemies destroyed: {_gm.TotalKills}\n" +
                $"Gold earned: {_gm.TotalEarned}";
            _nextLevelButton.gameObject.SetActive(won && _gm.NextLevelId() != null);
            SaveSystem.ClearRun();
        }

        void ShowOnly(GameObject panel)
        {
            _menuPanel.SetActive(panel == _menuPanel);
            _levelSelectPanel.SetActive(panel == _levelSelectPanel);
            _hudPanel.SetActive(panel == _hudPanel);
            _pausePanel.SetActive(panel == _pausePanel);
            _settingsPanel.SetActive(panel == _settingsPanel);
            _endPanel.SetActive(panel == _endPanel);
            if (panel != _hudPanel && _selPanel != null) _selPanel.SetActive(false);
        }
    }
}
