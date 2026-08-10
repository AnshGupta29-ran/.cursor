using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class CardArrayWrapper
{
    public Card[] cards;
}

public static class CardDatabase
{
    private static List<Card> _allCards;

    public static List<Card> AllCards
    {
        get
        {
            if (_allCards == null) Load();
            return _allCards;
        }
    }

    private static void Load()
    {
        var txt = Resources.Load<TextAsset>("cards");
        if (txt == null)
        {
            Debug.LogError("Card database not found in Resources/cards.json");
            _allCards = new List<Card>();
            return;
        }
        // JsonUtility cannot parse top-level array directly; wrap it
        var wrapper = JsonUtility.FromJson<CardArrayWrapper>("{\"cards\":" + txt.text + "}");
        _allCards = new List<Card>(wrapper.cards);
    }
}
