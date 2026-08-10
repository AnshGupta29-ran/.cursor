using UnityEngine;

public class GlacialPulse : MonoBehaviour
{
    public AIController AI;
    public PlayerController Player;
    private float _averageUnusedMana = 0f;
    private int _turnsSampled = 0;

    void Awake()
    {
        if (AI == null) AI = FindObjectOfType<AIController>();
        if (Player == null) Player = FindObjectOfType<PlayerController>();
    }

    // Called at end of each turn by GameManager
    public void UpdateDifficulty()
    {
        // Simple metric: how much mana the player leaves unused each turn
        int unused = Player.CurrentMana - Player.ManaPool.CurrentMana; // assuming CurrentMana tracks mana before crystallize
        _averageUnusedMana = (_averageUnusedMana * _turnsSampled + unused) / (_turnsSampled + 1);
        _turnsSampled++;
        // Adjust AI starting mana based on efficiency (more efficient player → tougher AI)
        AI.StartingMana = Mathf.Clamp(3 + (int)(_averageUnusedMana / 2), 3, AI.MaxMana);
        Debug.Log($"GlacialPulse updated AI starting mana to {AI.StartingMana} based on avg unused mana {_averageUnusedMana:F1}");
    }
}
