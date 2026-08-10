using UnityEngine;

public class ManaPool : MonoBehaviour
{
    public int CurrentMana = 0;
    public int MaxMana = 10;
    public int CrystallizedBuffTurns = 0; // simple buff duration

    public void GainMana(int amount)
    {
        CurrentMana = Mathf.Min(MaxMana, CurrentMana + amount);
    }

    public void Crystallize(int excessMana)
    {
        // Convert excess mana into a temporary attack buff lasting 2 turns (example)
        CrystallizedBuffTurns = 2;
        Debug.Log($"Crystallized {excessMana} mana into a temporary buff.");
    }

    void Update()
    {
        if (CrystallizedBuffTurns > 0)
        {
            CrystallizedBuffTurns--;
            if (CrystallizedBuffTurns == 0)
                Debug.Log("Crystallization buff expired.");
        }
    }
}
