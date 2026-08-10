using System;
using System.Collections.Generic;
using TD.Content;
using TD.Enemies;
using TD.Towers;
using UnityEngine;

namespace TD.Core
{
    public enum GameState { Menu, Playing, Paused, Won, Lost }

    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [Header("Difficulty multipliers (index = difficulty)")]
        public float[] enemyHealthMult = { 0.8f, 1f, 1.3f };
        public float[] enemySpeedMult = { 0.9f, 1f, 1.12f };
        public float[] startGoldMult = { 1.3f, 1f, 0.8f };
        public float[] rewardMult = { 1.2f, 1f, 0.9f };
        public float[] livesMult = { 1.5f, 1f, 1f };

        // Content
        public List<EnemyDefinition> enemyDefs = new List<EnemyDefinition>();
        public List<TowerDefinition> towerDefs = new List<TowerDefinition>();
        public List<LevelDefinition> levelDefs = new List<LevelDefinition>();
        readonly Dictionary<string, EnemyDefinition> _enemyById = new Dictionary<string, EnemyDefinition>();
        readonly Dictionary<string, TowerDefinition> _towerById = new Dictionary<string, TowerDefinition>();
        readonly Dictionary<string, LevelDefinition> _levelById = new Dictionary<string, LevelDefinition>();

        // Run state
        public GameState State { get; private set; } = GameState.Menu;
        public LevelDefinition CurrentLevel { get; private set; }
        public int Difficulty { get; private set; }
        public int Gold { get; private set; }
        public int Lives { get; private set; }
        public int WaveIndex { get; private set; } = -1; // -1 = before first wave
        public int WavesCompleted { get; private set; }
        public bool WaveInProgress { get; set; }
        public bool AutoStart { get; set; } = true;
        public int GameSpeed { get; private set; } = 1;

        public int Score { get; private set; }
        public int TotalKills { get; private set; }
        public int TotalEarned { get; private set; }
        public bool SpeedWasHeld { get; set; }

        // Events
        public event Action EconomyChanged;
        public event Action LivesChanged;
        public event Action WaveChanged;
        public event Action StateChanged;
        public event Action<EnemyDefinition, Vector3> EnemyKilled;
        public event Action<EnemyDefinition> EnemyLeaked;

        public float EnemyHealthMult => enemyHealthMult[Mathf.Clamp(Difficulty, 0, 2)];
        public float EnemySpeedMult => enemySpeedMult[Mathf.Clamp(Difficulty, 0, 2)];
        public float RewardMult => rewardMult[Mathf.Clamp(Difficulty, 0, 2)];

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            Application.targetFrameRate = 60;
        }

        public void SetContent(List<EnemyDefinition> enemies, List<TowerDefinition> towers, List<LevelDefinition> levels)
        {
            enemyDefs = enemies; towerDefs = towers; levelDefs = levels;
            _enemyById.Clear(); _towerById.Clear(); _levelById.Clear();
            foreach (var e in enemies) _enemyById[e.id] = e;
            foreach (var t in towers) _towerById[t.id] = t;
            foreach (var l in levels) _levelById[l.id] = l;
        }

        public EnemyDefinition GetEnemy(string id) => _enemyById.TryGetValue(id, out var e) ? e : null;
        public TowerDefinition GetTower(string id) => _towerById.TryGetValue(id, out var t) ? t : null;
        public LevelDefinition GetLevel(string id) => _levelById.TryGetValue(id, out var l) ? l : null;

        // ------------------------------------------------------------------
        // Game flow
        // ------------------------------------------------------------------
        public void StartLevel(string levelId, int difficulty)
        {
            var level = GetLevel(levelId);
            if (level == null) { Debug.LogError($"Unknown level '{levelId}'"); return; }
            CurrentLevel = level;
            Difficulty = Mathf.Clamp(difficulty, 0, 2);
            int d = Difficulty;
            Gold = Mathf.RoundToInt(level.startGold * startGoldMult[d]);
            Lives = Mathf.Max(1, Mathf.RoundToInt(level.startLives * livesMult[d]));
            WaveIndex = -1; WavesCompleted = 0; WaveInProgress = false;
            Score = 0; TotalKills = 0; TotalEarned = 0;
            GameSpeed = 1; Time.timeScale = 1f;
            SetState(GameState.Playing);
            EconomyChanged?.Invoke();
            LivesChanged?.Invoke();
            WaveChanged?.Invoke();
        }

        /// <summary>Advance to the next wave. Returns false if the game is over.</summary>
        public bool BeginNextWave()
        {
            if (State != GameState.Playing || WaveInProgress) return false;
            int next = WaveIndex + 1;
            if (CurrentLevel.waves == null || next >= CurrentLevel.waves.waves.Length) return false;
            WaveIndex = next;
            WaveInProgress = true;
            WaveChanged?.Invoke();
            return true;
        }

        public void OnWaveCleared()
        {
            WaveInProgress = false;
            WavesCompleted++;
            int bonus = 15 + WaveIndex * 3;
            AddGold(bonus);
            Score += 100 + WaveIndex * 25;
            WaveChanged?.Invoke();
            if (WavesCompleted >= CurrentLevel.waves.waves.Length)
            {
                SaveSystem.UnlockLevel(NextLevelId());
                SaveSystem.RecordResult(CurrentLevel.id, Difficulty, Score, true);
                SetState(GameState.Won);
            }
        }

        public string NextLevelId()
        {
            int i = levelDefs.IndexOf(CurrentLevel);
            return (i >= 0 && i + 1 < levelDefs.Count) ? levelDefs[i + 1].id : null;
        }

        void SetState(GameState s)
        {
            State = s;
            StateChanged?.Invoke();
        }

        public void PauseGame()
        {
            if (State != GameState.Playing) return;
            Time.timeScale = 0f;
            SetState(GameState.Paused);
        }

        public void ResumeGame()
        {
            if (State != GameState.Paused) return;
            Time.timeScale = GameSpeed;
            SetState(GameState.Playing);
        }

        public void CycleGameSpeed()
        {
            GameSpeed = GameSpeed >= 3 ? 1 : GameSpeed + 1;
            if (State == GameState.Playing) Time.timeScale = GameSpeed;
            WaveChanged?.Invoke(); // reuse to refresh HUD speed label
        }

        public void QuitToMenu()
        {
            Time.timeScale = 1f;
            SetState(GameState.Menu);
        }

        // ------------------------------------------------------------------
        // Economy
        // ------------------------------------------------------------------
        public bool CanAfford(int cost) => Gold >= cost;

        public bool SpendGold(int amount)
        {
            if (Gold < amount) return false;
            Gold -= amount;
            EconomyChanged?.Invoke();
            return true;
        }

        public void AddGold(int amount)
        {
            Gold += amount;
            TotalEarned += amount;
            EconomyChanged?.Invoke();
        }

        public void OnEnemyKilled(Enemy enemy)
        {
            int reward = Mathf.RoundToInt(enemy.Def.reward * RewardMult);
            AddGold(reward);
            TotalKills++;
            Score += reward * 2 + Mathf.RoundToInt(enemy.Def.health);
            EnemyKilled?.Invoke(enemy.Def, enemy.transform.position);
        }

        public void OnEnemyReachedBase(Enemy enemy)
        {
            Lives = Mathf.Max(0, Lives - enemy.Def.livesCost);
            Score = Mathf.Max(0, Score - 50);
            LivesChanged?.Invoke();
            EnemyLeaked?.Invoke(enemy.Def);
            if (Lives <= 0)
            {
                SaveSystem.RecordResult(CurrentLevel.id, Difficulty, Score, false);
                SetState(GameState.Lost);
            }
        }

        void Update()
        {
            if (State == GameState.Playing)
            {
                AddGoldFractional(CurrentLevel.goldTrickle * Time.deltaTime);
                if (Input.GetKeyDown(KeyCode.Space)) TogglePause();
                if (Input.GetKeyDown(KeyCode.F)) CycleGameSpeed();
                if (Input.GetKeyDown(KeyCode.Escape))
                {
                    if (BuildManager.Instance != null && BuildManager.Instance.CancelModes()) { }
                    else TogglePause();
                }
            }
            else if (State == GameState.Paused && Input.GetKeyDown(KeyCode.Space))
            {
                TogglePause();
            }
        }

        void TogglePause()
        {
            if (State == GameState.Playing) PauseGame();
            else if (State == GameState.Paused) ResumeGame();
        }

        float _goldFraction;
        void AddGoldFractional(float amount)
        {
            _goldFraction += amount;
            if (_goldFraction >= 1f)
            {
                int whole = Mathf.FloorToInt(_goldFraction);
                _goldFraction -= whole;
                Gold += whole;
                EconomyChanged?.Invoke();
            }
        }

        // ------------------------------------------------------------------
        // Mid-run save / load
        // ------------------------------------------------------------------
        public RunSnapshot CaptureSnapshot()
        {
            var snap = new RunSnapshot
            {
                levelId = CurrentLevel.id,
                difficulty = Difficulty,
                gold = Gold,
                lives = Lives,
                waveIndex = WaveIndex,
                wavesCompleted = WavesCompleted,
                score = Score,
                kills = TotalKills,
                earned = TotalEarned,
            };
            foreach (var tower in Tower.All)
                snap.towers.Add(new TowerSnapshot { towerId = tower.Def.id, nodeIndex = tower.Node.Index, level = tower.Level });
            foreach (var enemy in Enemy.All)
            {
                if (enemy == null) continue;
                snap.enemies.Add(new EnemySnapshot
                {
                    enemyId = enemy.Def.id,
                    segment = enemy.Segment,
                    progress = enemy.SegmentProgress,
                    health = enemy.Health,
                    slowRemaining = enemy.SlowRemaining,
                    slowAmount = enemy.CurrentSlowAmount,
                });
            }
            return snap;
        }

        public void RestoreSnapshot(RunSnapshot snap)
        {
            StartLevel(snap.levelId, snap.difficulty);
            Gold = snap.gold; Lives = snap.lives;
            WaveIndex = snap.waveIndex; WavesCompleted = snap.wavesCompleted;
            Score = snap.score; TotalKills = snap.kills; TotalEarned = snap.earned;
            _goldFraction = 0;
            // Towers and enemies are rebuilt by GameBootstrap after grid setup.
            EconomyChanged?.Invoke();
            LivesChanged?.Invoke();
            WaveChanged?.Invoke();
        }
    }
}
