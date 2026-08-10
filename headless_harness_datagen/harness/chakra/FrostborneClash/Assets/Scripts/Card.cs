using UnityEngine;
using System;

[Serializable]
public class Card
{
    public string Id;
    public string Name;
    public int ManaCost;
    public CardType Type;
}

public enum CardType { Creature, Spell, Artifact }
