using UnityEngine;
using UnityEngine.UI;

public class CardUI : MonoBehaviour
{
    public Image ArtImage;
    public Text NameText;
    public Text CostText;
    private Card _card;

    public void Setup(Card card)
    {
        _card = card;
        if (NameText != null) NameText.text = card.Name;
        if (CostText != null) CostText.text = card.ManaCost.ToString();
        // ArtImage could be set based on card ID if sprites are added later
    }

    // Called by UI drag‑and‑drop handler (not implemented here)
    public void OnDragEnd(Vector2 pointerPos)
    {
        // Convert screen pointer to board coordinates and ask PlayerController to play the card
        // Placeholder: actual implementation would be in a separate input manager
    }
}
