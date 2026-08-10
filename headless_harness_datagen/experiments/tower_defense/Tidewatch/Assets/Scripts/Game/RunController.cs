using System.Collections.Generic;
using Tidewatch.Core;
using UnityEngine;

namespace Tidewatch.Game
{
    /// <summary>
    /// Owns a single run: builds a GameSim from a level+difficulty (or a save), drives the
    /// sim clock with pause/1x/2x, and forwards sim events to visuals and audio. Sits
    /// between the engine-free sim and the MonoBehaviour view layer.
    /// </summary>
    public sealed class RunController : MonoBehaviour
    {
        public GameSim Sim { get; private set; }
        public LevelData Level { get; private set; }
        public DifficultyDef Difficulty { get; private set; }
        public bool CurrentEndless { get; private set; }
        public bool InRun => Sim != null && !Sim.GameOver;

        private GameBootstrap _boot;
        private GridView _gridView;
        private AudioManager _audio;
        private readonly Dictionary<int, EnemyView> _enemyViews = new Dictionary<int, EnemyView>();
        private readonly Dictionary<TowerInstance, TowerView> _towerViews = new Dictionary<TowerInstance, TowerView>();
        private float _speed = 1f;
        private bool _paused;
        private int _runSlot = -1;

        public float Speed => _speed;
        public bool Paused => _paused;

        public void Init(GameBootstrap boot, GridView gridView, AudioManager audio)
        {
            _boot = boot;
            _gridView = gridView;
            _audio = audio;
        }

        public void StartRun(LevelData level, DifficultyDef difficulty, bool endless, int slot = -1)
        {
            Level = level;
            Difficulty = difficulty;
            CurrentEndless = endless;
            _runSlot = slot;
            ulong runSeed = (ulong)System.DateTime.UtcNow.Ticks;
            var tide = new TideSystem(level.TideSchedule, difficulty.TideCadenceMult);
            Sim = new GameSim(_boot.Db, level.Grid, tide, level.Waves, difficulty, level.Id, runSeed, endless);
            WireSim();
            _gridView.BuildLevel(level.Grid);
            _gridView.SetTidePhase(tide.CurrentPhase);
            SetPaused(false);
            SetSpeed(_boot.Settings.speedPreference);
        }

        public void ResumeFromSave(RunSave save, LevelData level, DifficultyDef difficulty)
        {
            Level = level;
            Difficulty = difficulty;
            CurrentEndless = save.endless;
            _runSlot = -1;
            var tide = new TideSystem(level.TideSchedule, difficulty.TideCadenceMult);
            Sim = GameSim.FromSave(save, _boot.Db, level.Grid, tide, level.Waves, difficulty);
            WireSim();
            _gridView.BuildLevel(level.Grid);
            _gridView.SetTidePhase(tide.CurrentPhase);
            // Rebuild tower visuals.
            foreach (var t in Sim.Towers) SpawnTowerView(t);
            SetPaused(false);
        }

        private void WireSim()
        {
            Sim.Events.OnEnemySpawned += e => SpawnEnemyView(e);
            Sim.Events.OnEnemyDied += e => { _audio.PlayEnemyDeath(); RemoveEnemyView(e); };
            Sim.Events.OnEnemyLeaked += e => { _audio.PlayLanternDamage(); RemoveEnemyView(e); };
            Sim.Events.OnTowerFired += (t, target) => OnTowerFired(t, target);
            Sim.Events.OnTowerDisabled += t => { _audio.PlayTowerDisabled(); if (_towerViews.TryGetValue(t, out var v)) v.SetDisabled(true); };
            Sim.Events.OnTowerReenabled += t => { if (_towerViews.TryGetValue(t, out var v)) v.SetDisabled(false); };
            Sim.Events.OnTideTurn += phase => { _audio.PlayTideTurn(); _gridView.SetTidePhase(phase); };
            Sim.Events.OnTidecall += () => _audio.PlayTideTurn();
            Sim.Events.OnVictory += () => OnRunEnded(true);
            Sim.Events.OnDefeat += () => OnRunEnded(false);
            Sim.Events.OnWaveCleared += () => { SaveAtWaveBoundary(); };
        }

        public event System.Action<bool> OnRunEnded; // true = victory

        private void Update()
        {
            if (Sim == null || _paused || Sim.GameOver) return;
            float dt = Time.deltaTime * _speed;
            Sim.Tick(dt);
            SyncViews();
        }

        private void SyncViews()
        {
            foreach (var kv in _enemyViews) kv.Value.Sync(Time.deltaTime);
            foreach (var kv in _towerViews) kv.Value.Sync(Time.deltaTime);
        }

        // ---- build / interact passthrough (called by HUD) ----

        public bool TryBuild(string towerId, GridPos plot, out string reason)
        {
            bool ok = Sim.TryBuildTower(towerId, plot, out reason);
            if (ok)
            {
                var inst = Sim.Towers[Sim.Towers.Count - 1];
                SpawnTowerView(inst);
                _audio.PlayBuild();
            }
            return ok;
        }

        public bool TrySell(TowerInstance inst)
        {
            bool ok = Sim.TrySellTower(inst, out _);
            if (!ok) return false;
            if (_towerViews.TryGetValue(inst, out var v)) { Destroy(v.gameObject); _towerViews.Remove(inst); }
            _audio.PlaySell();
            return true;
        }

        public bool TryUpgrade(TowerInstance inst)
        {
            bool ok = Sim.TryUpgradeTower(inst);
            if (ok) { _audio.PlayUpgrade(); if (_towerViews.TryGetValue(inst, out var v)) v.RefreshTier(); }
            return ok;
        }

        public bool TryPickBranch(TowerInstance inst, bool a)
        {
            bool ok = Sim.TryPickBranch(inst, a);
            if (ok) { _audio.PlayUpgrade(); if (_towerViews.TryGetValue(inst, out var v)) v.RefreshTier(); }
            return ok;
        }

        public void CallWave()
        {
            if (Sim == null || Sim.WaveActive) return;
            _audio.PlayWaveHorn();
            Sim.TryCallWave();
        }

        public void SetPaused(bool p) { _paused = p; }
        public void SetSpeed(float s) { _speed = Mathf.Clamp(s, 1f, 2f); }
        public void ToggleSpeed() => SetSpeed(_speed >= 2f ? 1f : 2f);

        public TowerInstance TowerAt(GridPos p)
        {
            foreach (var t in Sim.Towers) if (t.Plot == p) return t;
            return null;
        }

        // ---- views ----

        private void SpawnEnemyView(Enemy e)
        {
            var view = EnemyView.Create(e, _boot.Db);
            _enemyViews[e.Id] = view;
        }

        private void RemoveEnemyView(Enemy e)
        {
            if (_enemyViews.TryGetValue(e.Id, out var v))
            {
                _enemyViews.Remove(e.Id);
                v.Despawn();
            }
        }

        private void SpawnTowerView(TowerInstance t)
        {
            var view = TowerView.Create(t, _boot.Db);
            _towerViews[t] = view;
        }

        private void OnTowerFired(TowerInstance t, Enemy target)
        {
            if (_towerViews.TryGetValue(t, out var v))
            {
                _audio.PlayTowerFire(t.DefId);
                v.Fire(target != null ? new Vector3(target.X, target.Y, 0f) : (Vector3?)null);
            }
        }

        // ---- save / end ----

        private void SaveAtWaveBoundary()
        {
            if (_runSlot < 0 || Sim == null) return;
            _boot.Saves.SaveRun(_runSlot, Sim.ToSave());
        }

        public void SaveNow(int slot)
        {
            _runSlot = slot;
            if (Sim != null) _boot.Saves.SaveRun(slot, Sim.ToSave());
        }

        private void OnRunEnded(bool victory)
        {
            // Update records + unlocks.
            if (victory)
            {
                if (!_boot.Meta.IsUnlocked(Level.Id)) _boot.Meta.unlockedLevels.Add(Level.Id);
                int idx = _boot.Levels.FindIndex(l => l.Id == Level.Id);
                if (idx >= 0 && idx + 1 < _boot.Levels.Count)
                {
                    string next = _boot.Levels[idx + 1].Id;
                    if (!_boot.Meta.IsUnlocked(next)) _boot.Meta.unlockedLevels.Add(next);
                }
            }
            var rec = _boot.Meta.GetOrAddRecord(Level.Id, Difficulty.Id);
            rec.bestWaveReached = Mathf.Max(rec.bestWaveReached, Sim.NextWaveIndex);
            if (victory)
            {
                rec.cleared = true;
                if (rec.bestTimeSeconds <= 0f || Sim.Elapsed < rec.bestTimeSeconds)
                    rec.bestTimeSeconds = Sim.Elapsed;
            }
            _boot.PersistMeta();
            // Clear the in-progress save for this slot.
            if (_runSlot >= 0) _boot.Saves.DeleteSlot(_runSlot);
            OnRunEnded?.Invoke(victory);
        }

        public void AbandonRun()
        {
            foreach (var v in _enemyViews.Values) if (v != null) Destroy(v.gameObject);
            foreach (var v in _towerViews.Values) if (v != null) Destroy(v.gameObject);
            _enemyViews.Clear();
            _towerViews.Clear();
            Sim = null;
            _gridView.ClearLevel();
        }
    }
}
