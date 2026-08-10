using UnityEngine;

namespace TD.Content
{
    public enum EnemyClass { Runner, Soldier, Tank, Swift, Flyer, Boss }

    [CreateAssetMenu(menuName = "TD/Enemy Definition", fileName = "NewEnemy")]
    public class EnemyDefinition : ScriptableObject
    {
        public string id = "enemy";
        public string displayName = "Enemy";
        public EnemyClass enemyClass = EnemyClass.Runner;

        [Header("Stats")]
        [Min(1f)] public float health = 30f;
        [Min(0.1f)] public float moveSpeed = 1.2f;
        [Range(0f, 0.9f), Tooltip("Fraction of incoming damage ignored (except armor-piercing)")]
        public float armor = 0f;
        [Min(1)] public int reward = 6;
        [Min(1)] public int livesCost = 1;

        [Header("Look")]
        public Color color = new Color(0.9f, 0.4f, 0.3f);
        [Min(0.2f)] public float scale = 1f;
        public bool flying = false;
        [Tooltip("Extra waypoint progress per second while invisible to towers")]
        public float stealth = 0f;
    }
}
