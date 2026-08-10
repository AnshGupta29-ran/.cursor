using UnityEngine;

namespace TD.Content
{
    [System.Serializable]
    public class WaveEntry
    {
        public EnemyDefinition enemy;
        [Min(1)] public int count = 6;
        [Min(0.05f)] public float interval = 0.9f;
        [Tooltip("Delay after previous entry finishes before this one starts")]
        public float startDelay = 0f;
        [Tooltip("Extra health multiplier on top of global wave scaling")]
        public float healthScale = 1f;
    }

    [System.Serializable]
    public class Wave
    {
        public string label = "Wave";
        public WaveEntry[] entries = new WaveEntry[1];
    }

    [CreateAssetMenu(menuName = "TD/Wave Config", fileName = "NewWaves")]
    public class WaveConfig : ScriptableObject
    {
        [Tooltip("Health multiplier applied per wave index (wave 1 is 0)")]
        public float healthScalePerWave = 0.08f;
        public Wave[] waves = new Wave[1];
    }
}
