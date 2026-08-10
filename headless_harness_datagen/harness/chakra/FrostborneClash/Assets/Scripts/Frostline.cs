using UnityEngine;

public class Frostline : MonoBehaviour
{
    public int TurnsPerAdvance = 2; // advance every 2 turns
    private int _turnCounter = 0;
    public Board Board;

    void Awake()
    {
        if (Board == null) Board = FindObjectOfType<Board>();
    }

    public void Advance()
    {
        _turnCounter++;
        if (_turnCounter >= TurnsPerAdvance)
        {
            _turnCounter = 0;
            // Shrink the board by 1 cell on each axis
            Board.ShrinkBoard(1);
            Debug.Log("Frostline advanced: board shrank.");
        }
    }
}
