using UnityEngine;
using System.Collections.Generic;

public class PlayerController : MonoBehaviour
{
    public int StartingMana = 3;
    public int MaxMana = 10;
    public int CurrentMana { get; private set; }
    public List<Card> Deck = new List<Card>();
    public List<Card> Hand = new List<Card>();
    public int HandSize = 5;
    public ManaPool ManaPool;
    public Board Board;
    public GameObject CardUIPrefab; // assigned via inspector
    public Transform HandArea; // UI parent for hand cards

    void Awake()
    {
        if (ManaPool == null) ManaPool = FindObjectOfType<ManaPool>();
        if (Board == null) Board = FindObjectOfType<Board>();
    }

    public void StartTurn()
    {
        DrawCards(HandSize - Hand.Count);
        // UI refresh could be triggered here
    }

    public void EndTurn()
    {
        // any end‑turn cleanup
    }

    void DrawCards(int count)
    {
        for (int i = 0; i < count && Deck.Count > 0; i++)
        {
            // simple draw from top of deck
            Card drawn = Deck[0];
            Deck.RemoveAt(0);
            Hand.Add(drawn);
            // instantiate UI element (placeholder, assumes prefab set)
            if (CardUIPrefab != null && HandArea != null)
            {
                GameObject go = Instantiate(CardUIPrefab, HandArea);
                var ui = go.GetComponent<CardUI>();
                if (ui != null) ui.Setup(drawn);
            }
        }
    }

    public bool PlayCard(Card card, Vector2Int boardPos)
    {
        if (card.ManaCost > CurrentMana) return false;
        if (!Board.IsPositionValid(boardPos)) return false;
        if (!Board.IsCellEmpty(boardPos)) return false;

        CurrentMana -= card.ManaCost;
        Hand.Remove(card);
        // instantiate card on board (prefab assumed)
        Board.PlaceCard(card, boardPos);
        return true;
    }

    public void CrystallizeExcessMana()
    {
        int excess = CurrentMana - MaxMana;
        if (excess > 0)
        {
            ManaPool.Crystallize(excess);
            CurrentMana = MaxMana;
        }
    }
}
