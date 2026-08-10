using System.Collections.Generic;
using Tidewatch.Core;
using UnityEngine;

namespace Tidewatch.Game
{
    /// <summary>
    /// Renders the tile grid from primitives: one quad per tile, colored by terrain and
    /// tide-flood state, plus a water plane that rises/falls with the tide. Also owns
    /// placement feedback (ghost, range ring) and screen<->grid conversion.
    /// </summary>
    public sealed class GridView : MonoBehaviour
    {
        private TileGrid _grid;
        private readonly Dictionary<GridPos, Renderer> _tiles = new Dictionary<GridPos, Renderer>();
        private Transform _root;
        private GameObject _water;
        private GameObject _ghost;
        private GameObject _rangeRing;
        private Material _tileMat;
        private Vector2Int _levelSize;

        private static readonly Color DeepWater = new Color(0.05f, 0.15f, 0.28f);
        private static readonly Color CausewayDry = new Color(0.62f, 0.55f, 0.42f);
        private static readonly Color CausewayWet = new Color(0.30f, 0.38f, 0.42f);
        private static readonly Color TrenchDry = new Color(0.45f, 0.40f, 0.34f);
        private static readonly Color TrenchWet = new Color(0.12f, 0.30f, 0.40f);
        private static readonly Color Rock = new Color(0.16f, 0.16f, 0.18f);
        private static readonly Color Plot = new Color(0.45f, 0.42f, 0.30f);
        private static readonly Color Gate = new Color(0.55f, 0.25f, 0.20f);
        private static readonly Color Base = new Color(0.95f, 0.80f, 0.30f);

        private void Awake()
        {
            _root = new GameObject("Tiles").transform;
            _root.SetParent(transform, false);
            _tileMat = new Material(Shader.Find("Standard"));
        }

        public void BuildLevel(TileGrid grid)
        {
            ClearLevel();
            _grid = grid;
            _levelSize = new Vector2Int(grid.Width, grid.Height);
            for (int x = 0; x < grid.Width; x++)
            {
                for (int y = 0; y < grid.Height; y++)
                {
                    var pos = new GridPos(x, y);
                    var tile = grid.Get(pos);
                    var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
                    go.transform.SetParent(_root, false);
                    go.transform.position = new Vector3(x + 0.5f, y + 0.5f, 0f);
                    go.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
                    // Remove collider; we do our own picking via camera ray math.
                    var col = go.GetComponent<Collider>();
                    if (col != null) Destroy(col);
                    var r = go.GetComponent<Renderer>();
                    r.material = new Material(_tileMat) { color = ColorFor(tile) };
                    _tiles[pos] = r;
                }
            }

            // Water plane that rises with the tide (visual only).
            _water = GameObject.CreatePrimitive(PrimitiveType.Quad);
            _water.transform.SetParent(transform, false);
            _water.transform.localScale = new Vector3(grid.Width, grid.Height, 1f);
            _water.transform.position = new Vector3(grid.Width / 2f, grid.Height / 2f, -0.1f);
            var wcol = _water.GetComponent<Collider>();
            if (wcol != null) Destroy(wcol);
            var wr = _water.GetComponent<Renderer>();
            wr.material = new Material(Shader.Find("Standard")) { color = new Color(0.1f, 0.3f, 0.5f, 0.35f) };

            // Camera framing.
            var cam = Camera.main;
            if (cam != null)
            {
                cam.transform.position = new Vector3(grid.Width / 2f, grid.Height / 2f, -10f);
                cam.orthographicSize = Mathf.Max(grid.Height / 2f + 1f, grid.Width / (2f * cam.aspect) + 1f);
            }
        }

        public void ClearLevel()
        {
            foreach (Transform c in _root) Destroy(c.gameObject);
            _tiles.Clear();
            if (_water != null) Destroy(_water);
            if (_ghost != null) Destroy(_ghost);
            if (_rangeRing != null) Destroy(_rangeRing);
            _grid = null;
        }

        public void SetTidePhase(TidePhase phase)
        {
            if (_grid == null) return;
            foreach (var kv in _tiles)
            {
                var tile = _grid.Get(kv.Key);
                kv.Value.material.color = ColorFor(tile);
            }
            if (_water != null)
            {
                float h = phase == TidePhase.High ? -0.05f : phase == TidePhase.Low ? 0.35f : 0.15f;
                var p = _water.transform.position;
                p.z = h;
                _water.transform.position = p;
            }
        }

        private static Color ColorFor(Tile t)
        {
            switch (t.Terrain)
            {
                case TerrainType.DeepWater: return DeepWater;
                case TerrainType.Causeway: return t.IsWater ? CausewayWet : CausewayDry;
                case TerrainType.Trench: return t.IsWater ? TrenchWet : TrenchDry;
                case TerrainType.BuildPlot: return Plot;
                case TerrainType.Gate: return Gate;
                case TerrainType.Base: return Base;
                default: return Rock;
            }
        }

        // ---- picking / placement ----

        public bool ScreenToGrid(Vector3 screen, out GridPos pos)
        {
            pos = default;
            var cam = Camera.main;
            if (cam == null || _grid == null) return false;
            Vector3 w = cam.ScreenToWorldPoint(screen);
            int x = Mathf.FloorToInt(w.x);
            int y = Mathf.FloorToInt(w.y);
            pos = new GridPos(x, y);
            return _grid.InBounds(pos);
        }

        /// <summary>Show a placement ghost with validity tint and a range ring.</summary>
        public void ShowGhost(GridPos pos, bool valid, float range, float illumination)
        {
            EnsureGhost();
            _ghost.transform.position = new Vector3(pos.X + 0.5f, pos.Y + 0.5f, -0.05f);
            var gr = _ghost.GetComponent<Renderer>();
            // Colorblind-safe: green = valid, red+striped-bright = invalid; ring always shown.
            gr.material.color = valid
                ? new Color(0.2f, 0.9f, 0.3f, 0.5f)
                : new Color(0.95f, 0.2f, 0.2f, 0.6f);
            float ringR = Mathf.Max(range, illumination);
            _rangeRing.transform.position = new Vector3(pos.X + 0.5f, pos.Y + 0.5f, -0.04f);
            _rangeRing.transform.localScale = new Vector3(ringR * 2f, ringR * 2f, 1f);
            _ghost.SetActive(true);
            _rangeRing.SetActive(true);
        }

        public void HideGhost()
        {
            if (_ghost != null) _ghost.SetActive(false);
            if (_rangeRing != null) _rangeRing.SetActive(false);
        }

        private void EnsureGhost()
        {
            if (_ghost == null)
            {
                _ghost = GameObject.CreatePrimitive(PrimitiveType.Quad);
                var c = _ghost.GetComponent<Collider>();
                if (c != null) Destroy(c);
                _ghost.GetComponent<Renderer>().material = new Material(Shader.Find("Standard"));
            }
            if (_rangeRing == null)
            {
                _rangeRing = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                var c = _rangeRing.GetComponent<Collider>();
                if (c != null) Destroy(c);
                _rangeRing.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                var r = _rangeRing.GetComponent<Renderer>();
                r.material = new Material(Shader.Find("Standard")) { color = new Color(1f, 1f, 1f, 0.08f) };
                _rangeRing.transform.localScale = new Vector3(1f, 0.01f, 1f);
            }
        }

        /// <summary>Base position in world space for the Lantern aura visual.</summary>
        public Vector3 BaseWorldPos()
        {
            if (_grid == null) return Vector3.zero;
            var b = _grid.BasePos;
            return new Vector3(b.X + 0.5f, b.Y + 0.5f, 0f);
        }
    }
}
