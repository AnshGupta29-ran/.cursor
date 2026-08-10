using System.Collections;
using System.Collections.Generic;
using TD.Content;
using TD.Core;
using UnityEngine;

namespace TD.Enemies
{
    /// <summary>
    /// Spawns wave entries over time, tracks living enemies, and reports wave
    /// completion back to the GameManager.
    /// </summary>
    public class WaveSpawner : MonoBehaviour
    {
        public static WaveSpawner Instance { get; private set; }

        EnemyPath _path;
        readonly HashSet<Enemy> _alive = new HashSet<Enemy>();
        Coroutine _spawnRoutine;

        public int EnemiesRemaining => _alive.Count;

        void Awake() { Instance = this; }

        public void SetPath(EnemyPath path) { _path = path; }

        public void StartNextWave()
        {
            var gm = GameManager.Instance;
            if (!gm.BeginNextWave()) return;
            var wave = gm.CurrentLevel.waves.waves[gm.WaveIndex];
            _spawnRoutine = StartCoroutine(SpawnWave(wave, gm.WaveIndex));
            AudioManager.Instance?.Play(SfxId.WaveStart);
        }

        IEnumerator SpawnWave(Wave wave, int waveIndex)
        {
            var gm = GameManager.Instance;
            float hpScale = 1f + gm.CurrentLevel.waves.healthScalePerWave * waveIndex;
            foreach (var entry in wave.entries)
            {
                if (entry.startDelay > 0f)
                    yield return new WaitForSeconds(entry.startDelay);
                for (int i = 0; i < entry.count; i++)
                {
                    Spawn(entry.enemy, hpScale * entry.healthScale);
                    yield return new WaitForSeconds(entry.interval);
                }
            }
            _spawnRoutine = null;
        }

        void Spawn(EnemyDefinition def, float healthScale)
        {
            var go = new GameObject($"enemy_{def.id}");
            go.transform.SetParent(transform, false);
            var enemy = go.AddComponent<Enemy>();
            enemy.Initialize(def, _path, healthScale);
            _alive.Add(enemy);
        }

        public void NotifyEnemyRemoved(Enemy enemy)
        {
            _alive.Remove(enemy);
            var gm = GameManager.Instance;
            if (gm.State == GameState.Playing && gm.WaveInProgress &&
                _spawnRoutine == null && _alive.Count == 0)
            {
                gm.OnWaveCleared();
            }
        }

        /// <summary>Restore enemies from a save snapshot (positions along the path).</summary>
        public void RestoreEnemies(List<EnemySnapshot> snapshots, float healthMult)
        {
            var gm = GameManager.Instance;
            foreach (var s in snapshots)
            {
                var def = gm.GetEnemy(s.enemyId);
                if (def == null) continue;
                var go = new GameObject($"enemy_{def.id}");
                go.transform.SetParent(transform, false);
                var enemy = go.AddComponent<Enemy>();
                enemy.Initialize(def, _path, healthMult);
                // fast-forward to the saved spot
                var pos = _path.PositionAt(0, out _, out _);
                float dist = 0f;
                for (int i = 1; i <= s.segment + 1 && i < _path.Points.Count; i++)
                    dist += Vector3.Distance(_path.Points[i - 1], _path.Points[i]);
                float segLen = s.segment + 1 < _path.Points.Count
                    ? Vector3.Distance(_path.Points[s.segment], _path.Points[s.segment + 1]) : 0f;
                dist = Mathf.Max(0f, dist - segLen) + segLen * s.progress;
                typeof(Enemy).GetProperty(nameof(Enemy.DistanceTravelled))!
                    .SetValue(enemy, dist);
                typeof(Enemy).GetProperty(nameof(Enemy.Health))!
                    .SetValue(enemy, s.health);
                if (s.slowRemaining > 0f) enemy.ApplySlow(s.slowAmount, s.slowRemaining);
                _alive.Add(enemy);
            }
        }

        public void ClearAll()
        {
            if (_spawnRoutine != null) { StopCoroutine(_spawnRoutine); _spawnRoutine = null; }
            foreach (var e in new List<Enemy>(_alive))
                if (e != null) Destroy(e.gameObject);
            _alive.Clear();
        }
    }
}
