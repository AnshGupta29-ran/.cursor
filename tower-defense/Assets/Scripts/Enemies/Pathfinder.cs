using System.Collections.Generic;
using UnityEngine;

namespace TD.Enemies
{
    /// <summary>
    /// Grid A* pathfinder. Used to smooth/validate the configured path and to
    /// re-route if a designer blocks a cell. 4-directional movement.
    /// </summary>
    public static class Pathfinder
    {
        class Node
        {
            public Vector2Int pos;
            public float g, f;
            public Node parent;
        }

        public static List<Vector2Int> FindPath(
            Vector2Int start, Vector2Int goal, int width, int height,
            System.Func<Vector2Int, bool> isWalkable)
        {
            var open = new List<Node>();
            var closed = new HashSet<Vector2Int>();
            var startNode = new Node { pos = start, g = 0, f = Heuristic(start, goal) };
            open.Add(startNode);
            var bestG = new Dictionary<Vector2Int, float> { [start] = 0 };

            while (open.Count > 0)
            {
                int best = 0;
                for (int i = 1; i < open.Count; i++)
                    if (open[i].f < open[best].f) best = i;
                var current = open[best];
                open.RemoveAt(best);

                if (current.pos == goal)
                    return Reconstruct(current);

                closed.Add(current.pos);
                foreach (var next in Neighbors(current.pos, width, height))
                {
                    if (closed.Contains(next) || !isWalkable(next)) continue;
                    float g = current.g + 1f;
                    if (bestG.TryGetValue(next, out float existing) && g >= existing) continue;
                    bestG[next] = g;
                    open.Add(new Node { pos = next, g = g, f = g + Heuristic(next, goal), parent = current });
                }
            }
            return null;
        }

        static float Heuristic(Vector2Int a, Vector2Int b) =>
            Mathf.Abs(a.x - b.x) + Mathf.Abs(a.y - b.y);

        static IEnumerable<Vector2Int> Neighbors(Vector2Int p, int w, int h)
        {
            if (p.x > 0) yield return new Vector2Int(p.x - 1, p.y);
            if (p.x < w - 1) yield return new Vector2Int(p.x + 1, p.y);
            if (p.y > 0) yield return new Vector2Int(p.x, p.y - 1);
            if (p.y < h - 1) yield return new Vector2Int(p.x, p.y + 1);
        }

        static List<Vector2Int> Reconstruct(Node node)
        {
            var path = new List<Vector2Int>();
            while (node != null) { path.Add(node.pos); node = node.parent; }
            path.Reverse();
            return path;
        }
    }
}
