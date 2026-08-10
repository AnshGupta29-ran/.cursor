using UnityEngine;

namespace TD.Content
{
    [CreateAssetMenu(menuName = "TD/Level Definition", fileName = "NewLevel")]
    public class LevelDefinition : ScriptableObject
    {
        public string id = "level1";
        public string displayName = "Level 1";
        [TextArea] public string description;

        [Header("Economy")]
        [Min(0)] public int startGold = 150;
        [Min(1)] public int startLives = 20;
        [Tooltip("Passive gold per second")]
        public float goldTrickle = 2f;
        [Min(1)] public int wavesNeeded = 8;

        [Header("Grid")]
        [Min(4)] public int gridWidth = 10;
        [Min(4)] public int gridHeight = 8;
        [Min(0.5f)] public float cellSize = 1f;
        [Tooltip("World-space cells where towers may be placed")]
        public Vector2Int[] buildNodes = new Vector2Int[0];

        [Header("Path")]
        [Tooltip("Waypoints (grid coords). First is the spawn, last is the base.")]
        public Vector2Int[] pathPoints = new Vector2Int[0];

        [Header("Content")]
        public WaveConfig waves;
    }
}
