using UnityEngine;

namespace TD.Towers
{
    /// <summary>
    /// A buildable pad on the grid. Hover/click feedback and occupancy tracking;
    /// BuildManager drives the actual placement and selection logic.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class BuildNode : MonoBehaviour
    {
        public int Index { get; set; }
        public Tower Occupant { get; private set; }
        public bool IsOccupied => Occupant != null;

        SpriteRenderer _sr;
        Color _baseColor;

        public void Initialize(int index, float cellSize)
        {
            Index = index;
            _sr = GetComponent<SpriteRenderer>();
            _sr.sprite = Core.SpriteFactory.RoundedSquare();
            _baseColor = new Color(1f, 1f, 1f, 0.10f);
            _sr.color = _baseColor;
            _sr.sortingOrder = 2;
            transform.localScale = Vector3.one * cellSize * 0.92f;
        }

        public void SetOccupied(Tower t) => Occupant = t;

        public void Clear()
        {
            Occupant = null;
            SetHighlight(false, false);
        }

        /// <summary>Hover feedback. valid=false tints red (e.g. can't afford).</summary>
        public void SetHighlight(bool on, bool valid = true)
        {
            if (_sr == null) return;
            _sr.color = !on ? _baseColor
                : valid ? new Color(0.4f, 1f, 0.5f, 0.35f)
                : new Color(1f, 0.35f, 0.3f, 0.35f);
        }
    }
}
