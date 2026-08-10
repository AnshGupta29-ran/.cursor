using System.Collections.Generic;
using TD.Content;
using TD.Enemies;
using TD.Towers;
using TD.UI;
using UnityEngine;

namespace TD.Core
{
    /// <summary>
    /// Scene composition root. Builds every manager, wires content into the
    /// GameManager, lays out the grid for a level, and handles the
    /// suspended-run restore flow. The scene itself only needs this one
    /// component on an empty GameObject.
    /// </summary>
    public class GameBootstrap : MonoBehaviour
    {
        GameManager _gm;
        EnemyPath _path;
        float _originX, _originY;

        void Awake()
        {
            Application.targetFrameRate = 60;

            // --- camera -----------------------------------------------------
            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 7f;
            cam.backgroundColor = new Color(0.09f, 0.11f, 0.16f);
            camGo.AddComponent<AudioListener>();
            var camCtl = camGo.AddComponent<CameraController>();

            // --- managers ---------------------------------------------------
            _gm = new GameObject("GameManager").AddComponent<GameManager>();
            new GameObject("AudioManager").AddComponent<AudioManager>();
            new GameObject("Effects").AddComponent<Effects>();
            new GameObject("WaveSpawner").AddComponent<WaveSpawner>();
            new GameObject("BuildManager").AddComponent<BuildManager>();

            var content = new GameObject("Content");
            _path = content.AddComponent<EnemyPath>();

            // --- content ----------------------------------------------------
            var enemies = DefaultContent.CreateEnemies();
            var byId = new Dictionary<string, EnemyDefinition>();
            foreach (var e in enemies) byId[e.id] = e;
            _gm.SetContent(enemies, DefaultContent.CreateTowers(), DefaultContent.CreateLevels(byId));

            // --- UI (needs an EventSystem for clicks) -----------------------
            var esGo = new GameObject("EventSystem");
            esGo.AddComponent<UnityEngine.EventSystems.EventSystem>();
            esGo.AddComponent<UnityEngine.EventSystems.StandaloneInputModule>();
            new GameObject("UI").AddComponent<UIManager>();

            _gm.StateChanged += OnStateChanged;
        }

        void OnDestroy()
        {
            if (_gm != null) _gm.StateChanged -= OnStateChanged;
        }

        /// <summary>Called by the UI to begin a fresh run.</summary>
        public void BeginLevel(string levelId, int difficulty)
        {
            SaveSystem.ClearRun();
            SaveSystem.Settings.lastDifficulty = difficulty;
            SaveSystem.Save();
            _gm.StartLevel(levelId, difficulty);
        }

        /// <summary>Called by the UI to resume the suspended run.</summary>
        public void ResumeSavedRun()
        {
            var snap = SaveSystem.Profile.run;
            if (snap == null) return;
            _gm.RestoreSnapshot(snap);
        }

        void OnStateChanged()
        {
            // Rebuild the grid on every run start; also lay out level 1 once
            // as a backdrop for the main menu.
            LayoutLevel();
        }

        void LayoutLevel()
        {
            var level = _gm.CurrentLevel;
            if (level == null)
            {
                // menu backdrop: lay out level 1 without a run
                level = _gm.levelDefs.Count > 0 ? _gm.levelDefs[0] : null;
                if (level == null) return;
            }

            _originX = -level.gridWidth * level.cellSize * 0.5f;
            _originY = -level.gridHeight * level.cellSize * 0.5f;

            // ground tiles
            var oldGround = GameObject.Find("Ground");
            if (oldGround != null) Destroy(oldGround);
            var ground = new GameObject("Ground");
            DrawGround(ground.transform, level);

            // path + nodes
            _path.Build(level, _originX, _originY);
            WaveSpawner.Instance.SetPath(_path);
            BuildManager.Instance.BuildNodes(level, _originX, _originY);

            // camera bounds
            var bounds = new Bounds(
                new Vector3(0, 0, 0),
                new Vector3(level.gridWidth * level.cellSize + 6f, level.gridHeight * level.cellSize + 4f, 10f));
            Camera.main.GetComponent<CameraController>().SetBounds(bounds);

            // rebuild a suspended run if the snapshot matches this level
            // (only when a run is actually active — not for the menu backdrop)
            var snap = SaveSystem.Profile.run;
            if (_gm.State == GameState.Playing && _gm.CurrentLevel != null && snap != null && snap.levelId == level.id)
            {
                foreach (var ts in snap.towers)
                {
                    var def = _gm.GetTower(ts.towerId);
                    if (def != null) BuildManager.Instance.RestoreTower(def, ts.nodeIndex, ts.level);
                }
                WaveSpawner.Instance.RestoreEnemies(snap.enemies, _gm.EnemyHealthMult);
                SaveSystem.ClearRun();
            }
        }

        void DrawGround(Transform parent, LevelDefinition level)
        {
            // checkerboard of grass tiles
            for (int x = 0; x < level.gridWidth; x++)
            {
                for (int y = 0; y < level.gridHeight; y++)
                {
                    var tile = new GameObject($"t{x}_{y}");
                    tile.transform.SetParent(parent, false);
                    tile.transform.position = EnemyPath.CellToWorld(new Vector2Int(x, y), level, _originX, _originY);
                    var sr = tile.AddComponent<SpriteRenderer>();
                    sr.sprite = SpriteFactory.Square();
                    bool dark = (x + y) % 2 == 0;
                    sr.color = dark ? new Color(0.16f, 0.24f, 0.18f) : new Color(0.18f, 0.27f, 0.20f);
                    sr.sortingOrder = -10;
                    tile.transform.localScale = Vector3.one * level.cellSize * 0.98f;
                }
            }
        }

        void OnApplicationQuit()
        {
            PersistRun();
        }

        void OnApplicationPause(bool paused)
        {
            if (paused) PersistRun();
        }

        /// <summary>Suspend the current run so it can be resumed next launch.</summary>
        void PersistRun()
        {
            if (_gm != null && (_gm.State == GameState.Playing || _gm.State == GameState.Paused))
                SaveSystem.SaveRun(_gm.CaptureSnapshot());
        }

        /// <summary>UI "Save & Quit" button.</summary>
        public void SaveAndQuitToMenu()
        {
            PersistRun();
            CleanupRun();
            _gm.QuitToMenu();
        }

        /// <summary>UI "Abandon Run" — drops the run without saving.</summary>
        public void AbandonRun()
        {
            SaveSystem.ClearRun();
            CleanupRun();
            _gm.QuitToMenu();
        }

        void CleanupRun()
        {
            WaveSpawner.Instance?.ClearAll();
            Projectile.ClearAll();
            foreach (var t in new List<Tower>(Tower.All))
            {
                if (t == null) continue;
                t.Node.Clear();
                Destroy(t.gameObject);
            }
            BuildManager.Instance?.Select(null);
        }
    }
}
