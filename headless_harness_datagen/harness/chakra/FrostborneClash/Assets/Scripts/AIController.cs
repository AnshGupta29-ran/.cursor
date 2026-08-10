using UnityEngine;
using System.Collections.Generic;

public class AIController : MonoBehaviour
{
    public int StartingMana = 3;
    public int MaxMana = 10;
    public int CurrentMana { get; private set; }
    public List<Card> Deck = new List<Card>();
    public List<Card> Hand = new List<Card>();
    public int HandSize = 5;
    public Board Board;
    public GameObject CardUIPrefab; // optional visual for debugging
    public Transform HandArea; // optional UI parent

    void Awake()
    {
        if (Board == null) Board = FindObjectOfType<Board>();
    }

    public void StartTurn()
    {
        DrawCards(HandSize - Hand.Count);
        // Simple deterministic AI: play the first playable card
        foreach (var card in new List<Card>(Hand))
        {
            // Find first empty cell within current safe area
            for (int x = 0; x < Board.Width; x++)
            {
                for (int y = 0; y < Board.Height; y++)
                {
                    Vector2Int pos = new Vector2Int(x, y);
                    if (Board.IsPositionValid(pos) && Board.IsCellEmpty(pos) && card.ManaCost <= CurrentMana)
                    {
                        PlayCard(card, pos);
                        goto EndLoop; // break out after playing one card per turn for simplicity
                    }
                }
            }
        }
    EndLoop:
        // AI could also choose to skip if nothing playable
    }

    public void EndTurn()
    {
        // No special end‑turn logic currently
    }

    void DrawCards(int count)
    {
        for (int i = 0; i < count && Deck.Count > 0; i++)
        {
            Card drawn = Deck[0];
            Deck.RemoveAt(0);
            Hand.Add(drawn);
            // Optional UI creation omitted
        }
    }

    bool PlayCard(Card card, Vector2Int pos)
    {
        if (card.ManaCost > CurrentMana) return false;
        if (!Board.IsPositionValid(pos) || !Board.IsCellEmpty(pos)) return false;
        CurrentMana -= card.ManaCost;
        Hand.Remove(card);
        Board.PlaceCard(card, pos);
        Debug.Log($"AI played {card.Name} at {pos}");
        return true;
    }
}
