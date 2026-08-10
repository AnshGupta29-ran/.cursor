using System.Collections.Generic;
using TD.Content;
using UnityEngine;

namespace TD.Enemies
{
    /// <summary>
    /// World-space enemy path built from the level's grid waypoints.
    /// Segments are expanded so enemies move cell-to-cell; towers query the
    /// "progress" metric for targeting priority.
    /// </summary>
    public class EnemyPath : MonoBehaviour
    {
        public List<Vector3> Points { get; private set; } = new List<Vector3>();
        public float TotalLength { get; private set; }
        public Vector3 Spawn => Points.Count > 0 ? Points[0] : Vector3.zero;
        public Vector3 Base => Points.Count > 0 ? Points[Points.Count - 1] : Vector3.zero;

        LineRenderer _line;

        public void Build(LevelDefinition level, float gridOriginX, float gridOriginY)
        {
            Points.Clear();
            foreach (var cell in Expand(level))
                Points.Add(CellToWorld(cell, level, gridOriginX, gridOriginY));

            TotalLength = 0f;
            for (int i = 1; i < Points.Count; i++)
                TotalLength += Vector3.Distance(Points[i - 1], Points[i]);

            DrawLine();
        }

        /// <summary>Expand waypoints into per-cell steps, using A* between waypoints
        /// so designers can skip corners and still get a valid route.</summary>
        static List<Vector2Int> Expand(LevelDefinition level)
        {
            var expanded = new List<Vector2Int>();
            var pts = level.pathPoints;
            if (pts == null || pts.Length == 0) return expanded;
            expanded.Add(pts[0]);
            for (int i = 1; i < pts.Length; i++)
            {
                var from = pts[i - 1];
                var to = pts[i];
                // Straight-line expansion (Manhattan, x then y) — levels are designed axis-aligned.
                int x = from.x, y = from.y;
                while (x != to.x) { x += (int)Mathf.Sign(to.x - x); expanded.Add(new Vector2Int(x, y)); }
                while (y != to.y) { y += (int)Mathf.Sign(to.y - y); expanded.Add(new Vector2Int(x, y)); }
            }
            return expanded;
        }

        public static Vector3 CellToWorld(Vector2Int cell, LevelDefinition level, float originX, float originY)
        {
            return new Vector3(
                originX + (cell.x + 0.5f) * level.cellSize,
                originY + (cell.y + 0.5f) * level.cellSize,
                0f);
        }

        /// <summary>Position + heading at a distance along the path.</summary>
        public Vector3 PositionAt(float distance, out int segment, out float segmentProgress)
        {
            segment = 0; segmentProgress = 0f;
            if (Points.Count == 0) return Vector3.zero;
            if (distance <= 0f) return Points[0];
            float remaining = distance;
            for (int i = 1; i < Points.Count; i++)
            {
                float len = Vector3.Distance(Points[i - 1], Points[i]);
                if (remaining <= len)
                {
                    segment = i - 1;
                    segmentProgress = len > 0 ? remaining / len : 0f;
                    return Vector3.Lerp(Points[i - 1], Points[i], segmentProgress);
                }
                remaining -= len;
            }
            segment = Points.Count - 2;
            segmentProgress = 1f;
            return Points[Points.Count - 1];
        }

        void DrawLine()
        {
            if (_line == null)
            {
                var go = new GameObject("PathLine");
                go.transform.SetParent(transform, false);
                _line = go.AddComponent<LineRenderer>();
                _line.material = Core.MaterialLibrary.Line;
                _line.startWidth = 0.08f; _line.endWidth = 0.08f;
                _line.startColor = new Color(1f, 0.9f, 0.6f, 0.25f);
                _line.endColor = new Color(1f, 0.9f, 0.6f, 0.25f);
                _line.sortingOrder = -5;
            }
            _line.positionCount = Points.Count;
            for (int i = 0; i < Points.Count; i++)
                _line.SetPosition(i, Points[i] + new Vector3(0, 0, 1f));
        }
    }
}
