using System.Collections.Generic;
using Tidewatch.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Tidewatch.Game
{
    /// <summary>
    /// In-run HUD: Salvage (with Reserve interest preview), Lantern Light, wave counter +
    /// next-wave preview, Tide Meter with phase + time-to-turn, speed controls, build bar,
    /// placement ghost, and the tower inspector. Handles placement input and hotkeys.
    /// </summary>
    public sealed class HudController : MonoBehaviour
    {
        private GameBootstrap _boot;
        private RunController _run;
        private AudioManager _audio;
        private ScreenManager _screens;

        private RectTransform _root;
        private Text _salvageText;
        private Text _interestText;
        private Text _lanternText;
        private Text _waveText;
        private Text _tideText;
        private RectTransform _tideFill;
        private Text _speedText;
        private Text _hintText;
        private GameObject _inspector;
        private GameObject _buildBar;
        private GameObject _banner;

        private string _selectedTowerId;
        private TowerInstance _selectedTower;
        private float _hintTimer;
        private float _bannerTimer;
        private float _reservePreview;

        private readonly string[] _hotbar = {
            TowerIds.BeaconSpire, TowerIds.FlareMortar, TowerIds.PrismArray,
            TowerIds.HarpoonBallista, TowerIds.FogBell
        };

        public void Init(GameBootstrap boot, RunController run, AudioManager audio, ScreenManager screens)
        {
            _boot = boot;
            _run = run;
            _audio = audio;
            _screens = screens;
            _screens.AttachHud(this);
            _root = (RectTransform)transform;
            BuildHud();
            gameObject.SetActive(false);
        }

        public void OnRunStarted()
        {
            _selectedTowerId = null;
            _selectedTower = null;
            HideInspector();
            UpdateAll();
        }

        // ------------------------------------------------------------------
        // HUD construction
        // ------------------------------------------------------------------

        private void BuildHud()
        {
            // Top bar.
            var top = Ui.Panel(_root, "TopBar", new Color(0.05f, 0.07f, 0.10f, 0.85f));
            Ui.Frac(top, 0f, 0.94f, 1f, 1f);
            _salvageText = MakeHudLabel(top, "Salvage", new Vector2(0.02f, 0.5f), TextAnchor.MiddleLeft);
            _interestText = MakeHudLabel(top, "Interest", new Vector2(0.16f, 0.5f), TextAnchor.MiddleLeft);
            _interestText.fontSize = 16;
            _interestText.color = Ui.SubText;
            _lanternText = MakeHudLabel(top, "Lantern", new Vector2(0.30f, 0.5f), TextAnchor.MiddleLeft);
            _waveText = MakeHudLabel(top, "Wave", new Vector2(0.46f, 0.5f), TextAnchor.MiddleLeft);
            _tideText = MakeHudLabel(top, "Tide", new Vector2(0.60f, 0.5f), TextAnchor.MiddleLeft);

            // Tide meter bar.
            var tideBarBg = Ui.Panel(top, "TideBarBg", Ui.PanelBgLight);
            tideBarBg.Anchored(new Vector2(0.74f, 0.5f), new Vector2(160, 18));
            var tideFill = Ui.Panel(tideBarBg, "Fill", Ui.Accent);
            Ui.Frac(tideFill, 0f, 0f, 1f, 1f);
            tideFill.pivot = new Vector2(0f, 0.5f);
            _tideFill = tideFill;

            // Speed + menu buttons.
            var speedBtn = Ui.Button(top, "Speed", "1×", () => { _run.ToggleSpeed(); _audio.PlayUi(); });
            speedBtn.GetComponent<RectTransform>().Anchored(new Vector2(0.90f, 0.5f), new Vector2(70, 40));
            _speedText = speedBtn.GetComponentInChildren<Text>();
            var pauseBtn = Ui.Button(top, "Menu", "☰", () => { _run.SetPaused(true); _audio.PlayUi(); _screens.ShowPause(); });
            pauseBtn.GetComponent<RectTransform>().Anchored(new Vector2(0.965f, 0.5f), new Vector2(60, 40));

            // Build bar (bottom).
            _buildBar = Ui.Panel(_root, "BuildBar", new Color(0.05f, 0.07f, 0.10f, 0.85f)).gameObject;
            Ui.Frac((RectTransform)_buildBar.transform, 0f, 0f, 1f, 0.10f);
            float x = 0.06f;
            for (int i = 0; i < _hotbar.Length; i++)
            {
                string id = _hotbar[i];
                if (!_boot.Db.TryGetTower(id, out var def)) continue;
                int hotkey = i + 1;
                var btn = Ui.Button(_buildBar.transform, id,
                    $"{hotkey}  {def.DisplayName}\n{def.Tiers[0].Cost} Salvage", () => SelectTowerToBuild(id));
                btn.GetComponent<RectTransform>().Anchored(new Vector2(x, 0.5f), new Vector2(200, 56));
                btn.name = "build_" + id;
                x += 0.115f;
            }
            // Call wave button.
            var callBtn = Ui.Button(_buildBar.transform, "CallWave", "Call Wave  [Space]", () =>
            {
                _run.CallWave();
            }, Ui.Accent * 0.5f);
            callBtn.GetComponent<RectTransform>().Anchored(new Vector2(0.80f, 0.5f), new Vector2(220, 56));

            // Hint text (placement feedback).
            _hintText = Ui.Label(_root, "Hint", "", 22);
            _hintText.rectTransform.Anchored(new Vector2(0.5f, 0.13f), new Vector2(800, 36));
            _hintText.color = Ui.Invalid;

            // Tide warning banner.
            _banner = Ui.Panel(_root, "Banner", new Color(0.9f, 0.7f, 0.2f, 0.9f)).gameObject;
            _banner.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, 0.86f), new Vector2(560, 46));
            var bannerTxt = Ui.Label(_banner.transform, "Text", "The tide is turning!", 24);
            Ui.Stretch(bannerTxt.rectTransform);
            bannerTxt.color = Color.black;
            _banner.SetActive(false);
        }

        private Text MakeHudLabel(Transform parent, string name, Vector2 pos, TextAnchor anchor)
        {
            var t = Ui.Label(parent, name, "", 24, anchor);
            t.rectTransform.Anchored(pos, new Vector2(280, 40));
            return t;
        }

        // ------------------------------------------------------------------
        // Per-frame update + input
        // ------------------------------------------------------------------

        private void Update()
        {
            // The HUD GameObject is disabled while menus are up, so Update only runs in-run.
            if (_run.Sim == null) return;
            HandleInput();
            UpdateAll();
            TickHintAndBanner();
        }

        private void HandleInput()
        {
            // Hotkeys 1-5 select towers.
            for (int i = 0; i < _hotbar.Length; i++)
            {
                if (Input.GetKeyDown(KeyCode.Alpha1 + i))
                    SelectTowerToBuild(_hotbar[i]);
            }
            if (Input.GetKeyDown(KeyCode.Space)) _run.CallWave();
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (_selectedTowerId != null) CancelPlacement();
                else if (_selectedTower != null) HideInspector();
                else { _run.SetPaused(true); _screens.ShowPause(); }
            }

            // Mouse: hover ghost + click to place / select.
            if (_selectedTowerId != null)
            {
                if (_run.Sim != null && FindGridView() != null &&
                    FindGridView().ScreenToGrid(Input.mousePosition, out var pos))
                {
                    var def = _boot.Db.GetTower(_selectedTowerId);
                    bool valid = PlacementValid(pos, out _);
                    var stats = def.Tiers[0];
                    FindGridView().ShowGhost(pos, valid, stats.Range, stats.IlluminationRadius);
                }
                if (Input.GetMouseButtonDown(0)) TryPlaceAtMouse();
                if (Input.GetMouseButtonDown(1)) CancelPlacement();
            }
            else if (Input.GetMouseButtonDown(0) && _run.Sim != null)
            {
                // Select a tower to inspect.
                if (FindGridView() != null && FindGridView().ScreenToGrid(Input.mousePosition, out var pos))
                {
                    var t = _run.TowerAt(pos);
                    if (t != null) ShowInspector(t);
                    else HideInspector();
                }
            }
        }

        private GridView _gridViewCache;
        private GridView FindGridView()
        {
            if (_gridViewCache == null) _gridViewCache = FindObjectOfType<GridView>();
            return _gridViewCache;
        }

        private bool PlacementValid(GridPos pos, out string reason)
        {
            reason = null;
            var def = _boot.Db.GetTower(_selectedTowerId);
            var tile = _run.Sim.Grid.Get(pos);
            if (tile == null || tile.Terrain != TerrainType.BuildPlot) { reason = "Must build on a raised plot."; return false; }
            if (tile.OccupiedByTowerId != null) { reason = "Plot already occupied."; return false; }
            if (!_run.Sim.Economy.CanAfford(def.Tiers[0].Cost)) { reason = "Not enough Salvage."; return false; }
            return true;
        }

        private void TryPlaceAtMouse()
        {
            if (FindGridView() == null) return;
            if (!FindGridView().ScreenToGrid(Input.mousePosition, out var pos)) return;
            if (_run.TryBuild(_selectedTowerId, pos, out var reason))
            {
                ShowHint("", 0f);
            }
            else
            {
                ShowHint(reason, 2f);
            }
        }

        private void SelectTowerToBuild(string id)
        {
            _selectedTowerId = id;
            _selectedTower = null;
            HideInspector();
            _audio.PlayUi();
            RefreshBuildBarSelection();
        }

        private void CancelPlacement()
        {
            _selectedTowerId = null;
            if (FindGridView() != null) FindGridView().HideGhost();
            RefreshBuildBarSelection();
        }

        private void RefreshBuildBarSelection()
        {
            foreach (var id in _hotbar)
            {
                var t = _buildBar.transform.Find("build_" + id);
                if (t != null)
                {
                    var img = t.GetComponent<Image>();
                    img.color = id == _selectedTowerId ? Ui.Accent * 0.7f : Ui.PanelBgLight;
                }
            }
        }

        // ------------------------------------------------------------------
        // HUD refresh
        // ------------------------------------------------------------------

        private void UpdateAll()
        {
            var sim = _run.Sim;
            if (sim == null) return;

            _salvageText.text = $"Salvage  {sim.Economy.Salvage}";
            // Reserve interest preview.
            int dividend = (int)(sim.Economy.Salvage * sim.Economy.ReserveInterestRate);
            if (dividend > sim.Economy.ReserveInterestCap) dividend = sim.Economy.ReserveInterestCap;
            _interestText.text = $"+{dividend} next wave (Reserve)";
            _lanternText.text = $"Lantern Light  {sim.LanternLight}/{sim.LanternLightMax}";
            _waveText.text = sim.Endless
                ? $"Wave {sim.NextWaveIndex}  (∞)"
                : $"Wave {sim.NextWaveIndex}/{sim.WaveCount}";
            _tideText.text = $"Tide: {sim.Tide.CurrentPhase}  {sim.Tide.TimeToNextTurn:0}s";
            float f = sim.Tide.CurrentPhaseDuration > 0 ? sim.Tide.PhaseClock / sim.Tide.CurrentPhaseDuration : 0f;
            _tideFill.anchorMax = new Vector2(Mathf.Clamp01(f), 1f);
            _speedText.text = _run.Speed >= 2f ? "2×" : "1×";

            // Tide-turn warning banner 5s ahead.
            if (sim.Tide.TimeToNextTurn <= 5f && sim.Tide.TimeToNextTurn > 0f)
                ShowBanner($"The tide turns to {sim.Tide.PeekPhase(1)} soon!", 0.2f);
        }

        private void ShowHint(string msg, float duration)
        {
            _hintText.text = msg;
            _hintTimer = duration;
        }

        private void ShowBanner(string msg, float duration)
        {
            if (_bannerTimer > Time.unscaledTime) return;
            _banner.SetActive(true);
            var txt = _banner.GetComponentInChildren<Text>();
            if (txt != null) txt.text = msg;
            _bannerTimer = Time.unscaledTime + duration + 1f;
        }

        private void TickHintAndBanner()
        {
            if (_hintTimer > 0f)
            {
                _hintTimer -= Time.unscaledDeltaTime;
                if (_hintTimer <= 0f) _hintText.text = "";
            }
            if (_banner.activeSelf && Time.unscaledTime > _bannerTimer)
                _banner.SetActive(false);
        }

        // ------------------------------------------------------------------
        // Tower inspector
        // ------------------------------------------------------------------

        private void ShowInspector(TowerInstance t)
        {
            _selectedTower = t;
            CancelPlacement();
            if (_inspector != null) Destroy(_inspector);
            _inspector = Ui.Panel(_root, "Inspector", Ui.PanelBg).gameObject;
            ((RectTransform)_inspector.transform).Anchored(new Vector2(0.13f, 0.42f), new Vector2(300, 560));

            var def = _boot.Db.GetTower(t.DefId);
            var stats = t.ResolveStats();
            float y = 0.95f;
            AddInspectorLabel($"{def.DisplayName}", 26, ref y);
            AddInspectorLabel($"Tier {t.Tier + 1}" + (t.BranchId != null ? $" · {BranchName(t)}" : ""), 20, ref y);
            y -= 0.02f;
            AddInspectorLabel(StatLine(def, stats), 18, ref y, 90);
            AddInspectorLabel($"Targeting:", 18, ref y);

            // Targeting priority buttons.
            string[] prNames = { "First", "Last", "Strongest", "Closest" };
            float px = 0.5f;
            for (int i = 0; i < 4; i++)
            {
                var pr = (TargetPriority)i;
                var b = Ui.Button(_inspector.transform, "pr" + i, prNames[i], () =>
                {
                    t.Priority = pr;
                    _audio.PlayUi();
                    ShowInspector(t);
                });
                b.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, y), new Vector2(220, 36));
                if (t.Priority == pr) b.GetComponent<Image>().color = Ui.Accent * 0.6f;
                y -= 0.075f;
            }
            y -= 0.02f;

            // Upgrade / branch.
            if (t.Tier < t.MaxTier)
            {
                int cost = t.NextUpgradeCost;
                AddButton($"Upgrade  ({cost})", () => { if (_run.TryUpgrade(t)) ShowInspector(t); }, ref y);
            }
            else if (t.BranchId == null)
            {
                AddInspectorLabel("Choose a capstone:", 18, ref y);
                AddButton($"{def.BranchA.DisplayName}  ({t.BranchCost(true)})",
                    () => { if (_run.TryPickBranch(t, true)) ShowInspector(t); }, ref y);
                AddButton($"{def.BranchB.DisplayName}  ({t.BranchCost(false)})",
                    () => { if (_run.TryPickBranch(t, false)) ShowInspector(t); }, ref y);
            }

            // Sell.
            int refund = _run.Sim.Economy.SellRefund(t.TotalInvested);
            AddButton($"Sell  (+{refund})", () =>
            {
                _run.TrySell(t);
                HideInspector();
            }, ref y, Ui.Invalid * 0.7f);
        }

        private string BranchName(TowerInstance t)
        {
            var b = t.ActiveBranch();
            return b != null ? b.DisplayName : "";
        }

        private string StatLine(TowerDef def, TowerTierStats s)
        {
            var sb = new System.Text.StringBuilder();
            if (def.DealsDamage) sb.AppendLine($"Damage {s.Damage:0.#}   Rate {s.FireRate:0.#}/s");
            sb.AppendLine($"Range {s.Range:0.#}");
            if (s.IlluminationRadius > 0) sb.AppendLine($"Illumination {s.IlluminationRadius:0.#}");
            if (s.SlowPct > 0) sb.AppendLine($"Slow {s.SlowPct * 100:0}%");
            if (s.ChainArcs > 0) sb.AppendLine($"Chain arcs {s.ChainArcs}");
            if (s.Pierce > 0) sb.AppendLine($"Pierce {s.Pierce}");
            return sb.ToString();
        }

        private void AddInspectorLabel(string text, int size, ref float y, float height = 34)
        {
            var t = Ui.Label(_inspector.transform, "lbl" + y, text, size, TextAnchor.UpperCenter);
            t.rectTransform.Anchored(new Vector2(0.5f, y), new Vector2(280, height));
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            y -= height / 560f + 0.01f;
        }

        private void AddButton(string label, System.Action onClick, ref float y, Color? bg = null)
        {
            var b = Ui.Button(_inspector.transform, "btn" + y, label, onClick, bg);
            b.GetComponent<RectTransform>().Anchored(new Vector2(0.5f, y), new Vector2(250, 44));
            y -= 0.09f;
        }

        private void HideInspector()
        {
            _selectedTower = null;
            if (_inspector != null) { Destroy(_inspector); _inspector = null; }
        }
    }
}
