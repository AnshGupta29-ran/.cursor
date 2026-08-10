using System.Collections.Generic;
using System.IO;
using Tidewatch.Core;
using UnityEngine;

namespace Tidewatch.Game
{
    /// <summary>
    /// Entry point. Builds the whole game at runtime so the project ships with a single
    /// scene and no hand-wired prefabs: camera, light, grid view, HUD, screens, audio.
    /// Attach to one GameObject in the only scene.
    /// </summary>
    public sealed class GameBootstrap : MonoBehaviour
    {
        public static GameBootstrap Instance { get; private set; }

        public ContentDb Db { get; private set; }
        public List<LevelData> Levels { get; private set; }
        public SaveStore Saves { get; private set; }
        public MetaProgress Meta { get; private set; }
        public GameSettings Settings { get; private set; }

        private GridView _gridView;
        private HudController _hud;
        private ScreenManager _screens;
        private AudioManager _audio;
        private RunController _run;

        private void Awake()
        {
            if (Instance != null) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            Application.targetFrameRate = 60;
            QualitySettings.vSyncCount = 1;

            // Content + persistence.
            Db = ContentLoader.LoadDb();
            Levels = ContentLoader.LoadAllLevels(Db);
            Saves = new SaveStore(Application.persistentDataPath, new UnityJson());
            Meta = Saves.LoadMeta();
            Settings = Saves.LoadSettings();

            // Unlock the first level by default.
            if (Levels.Count > 0 && !Meta.IsUnlocked(Levels[0].Id))
            {
                Meta.unlockedLevels.Add(Levels[0].Id);
                Saves.SaveMeta(Meta);
            }

            SetupScene();

            _audio = gameObject.AddComponent<AudioManager>();
            _audio.Init(Settings);

            _run = gameObject.AddComponent<RunController>();
            _run.Init(this, _gridView, _audio);

            _screens = GetComponentInChildren<ScreenManager>();
            _screens.Init(this, _run, _audio);

            _hud = GetComponentInChildren<HudController>();
            _hud.Init(this, _run, _audio, _screens);

            _screens.ShowMainMenu();
        }

        private void SetupScene()
        {
            // Camera.
            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 6f;
            cam.transform.position = new Vector3(0f, 0f, -10f);
            cam.backgroundColor = new Color(0.05f, 0.08f, 0.12f);
            camGo.AddComponent<AudioListener>();

            // Directional light for primitives.
            var lightGo = new GameObject("Moonlight");
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Directional;
            light.color = new Color(0.7f, 0.8f, 1f);
            light.intensity = 1.1f;
            lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

            // Grid view root.
            var gridGo = new GameObject("GridView");
            _gridView = gridGo.AddComponent<GridView>();

            // UI canvas.
            var canvasGo = new GameObject("UI");
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.AddComponent<UnityEngine.UI.CanvasScaler>();
            scaler.uiScaleMode = UnityEngine.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            canvasGo.AddComponent<UnityEngine.UI.GraphicRaycaster>();

            // Event system.
            if (FindObjectOfType<UnityEngine.EventSystems.EventSystem>() == null)
            {
                var esGo = new GameObject("EventSystem");
                esGo.AddComponent<UnityEngine.EventSystems.EventSystem>();
                esGo.AddComponent<UnityEngine.EventSystems.StandaloneInputModule>();
            }

            var screensGo = new GameObject("Screens");
            screensGo.transform.SetParent(canvasGo.transform, false);
            _screens = screensGo.AddComponent<ScreenManager>();

            var hudGo = new GameObject("HUD");
            hudGo.transform.SetParent(canvasGo.transform, false);
            _hud = hudGo.AddComponent<HudController>();
        }

        public void PersistMeta() => Saves.SaveMeta(Meta);
        public void PersistSettings() => Saves.SaveSettings(Settings);

        public LevelData GetLevel(string id)
        {
            foreach (var l in Levels) if (l.Id == id) return l;
            return null;
        }
    }
}
