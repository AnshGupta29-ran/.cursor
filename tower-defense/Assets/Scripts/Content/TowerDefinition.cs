using UnityEngine;

namespace TD.Content
{
    /// <summary>One upgrade level of a tower: its combat stats, cost and look.</summary>
    [System.Serializable]
    public class TowerLevel
    {
        [Min(0)] public int cost = 50;
        [Min(0f)] public float damage = 10f;
        [Min(0.1f)] public float range = 2.5f;
        [Tooltip("Shots per second")] public float fireRate = 1f;
        [Min(0.1f)] public float projectileSpeed = 12f;
        [Tooltip("Seconds between multi-shot bursts (0 = single shot)")]
        public float burstInterval = 0f;
        [Min(0f)] public float splashRadius = 0f;
        [Range(0f, 0.9f), Tooltip("Movement slow applied on hit (fraction)")]
        public float slowAmount = 0f;
        [Min(0f)] public float slowDuration = 0f;
        [Tooltip("Extra damage to armored enemies (multiplier)")]
        public float armorPierce = 0f;
        public Color bodyColor = Color.gray;
        [Min(0.5f)] public float scale = 1f;
    }

    [CreateAssetMenu(menuName = "TD/Tower Definition", fileName = "NewTower")]
    public class TowerDefinition : ScriptableObject
    {
        public string id = "tower";
        public string displayName = "Tower";
        [TextArea] public string description;
        [TextArea] public string upgradeHint;
        public Targeting targeting = Targeting.First;
        [Min(1f)] public float footprint = 1f;
        public TowerLevel[] levels = new TowerLevel[1];

        public int MaxLevel => levels.Length;
        public int BuildCost => levels.Length > 0 ? levels[0].cost : 0;
        public int TotalInvested(int level)
        {
            int total = 0;
            for (int i = 0; i <= level && i < levels.Length; i++) total += levels[i].cost;
            return total;
        }
    }

    public enum Targeting { First, Last, Strongest, Closest }
}
