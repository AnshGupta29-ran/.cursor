using System.Collections.Generic;

namespace Tidewatch.Core
{
    /// <summary>
    /// Grid pathfinding per movement class over the *current* tide-state graph.
    /// BFS from the base backwards produces a distance field; enemies then walk downhill.
    /// This is O(W*H) per recompute and handles multiple gates/lanes, and gives every
    /// enemy a next-step without per-enemy A*. Recomputed whenever the tide turns.
    /// </summary>
    public sealed class PathField
    {
        private readonly TileGrid _grid;
        private readonly MoveClass _moveClass;
        // distance[x,y] = steps to base, -1 = unreachable
        private readonly int[,] _dist;

        public PathField(TileGrid grid, MoveClass moveClass)
        {
            _grid = grid;
            _moveClass = moveClass;
            _dist = new int[grid.Width, grid.Height];
            Recompute();
        }

        public MoveClass Class => _moveClass;

        /// <summary>Rebuild the distance field from the base over current walkability.</summary>
        public void Recompute()
        {
            for (int x = 0; x < _grid.Width; x++)
                for (int y = 0; y < _grid.Height; y++)
                    _dist[x, y] = -1;

            var queue = new Queue<GridPos>();
            GridPos b = _grid.BasePos;
            if (!_grid.InBounds(b)) return;
            _dist[b.X, b.Y] = 0;
            queue.Enqueue(b);

            while (queue.Count > 0)
            {
                var cur = queue.Dequeue();
                int d = _dist[cur.X, cur.Y];
                foreach (var n in _grid.Neighbours(cur))
                {
                    if (_dist[n.X, n.Y] != -1) continue;
                    if (!_grid.IsWalkable(n, _moveClass)) continue;
                    _dist[n.X, n.Y] = d + 1;
                    queue.Enqueue(n);
                }
            }
        }

        public bool IsReachable(GridPos p) =>
            _grid.InBounds(p) && _dist[p.X, p.Y] >= 0;

        public int Distance(GridPos p) =>
            _grid.InBounds(p) ? _dist[p.X, p.Y] : -1;

        /// <summary>
        /// Best next step from p toward the base: a walkable neighbour with strictly
        /// lower distance. Returns false if p is unreachable or already at base.
        /// </summary>
        public bool TryGetNextStep(GridPos p, out GridPos next)
        {
            next = p;
            if (!_grid.InBounds(p)) return false;
            int d = _dist[p.X, p.Y];
            if (d <= 0) return false; // at base or unreachable

            GridPos best = p;
            int bestD = d;
            foreach (var n in _grid.Neighbours(p))
            {
                int nd = _grid.InBounds(n) ? _dist[n.X, n.Y] : -1;
                if (nd >= 0 && nd < bestD && _grid.IsWalkable(n, _moveClass))
                {
                    bestD = nd;
                    best = n;
                }
            }
            if (bestD >= d) return false; // no downhill step (surrounded)
            next = best;
            return true;
        }

        /// <summary>
        /// Full path from a gate/position to the base as a list of grid steps, or empty
        /// if unreachable. Used by tests and by enemies to seed their waypoint list.
        /// </summary>
        public List<GridPos> BuildPath(GridPos from)
        {
            var path = new List<GridPos>();
            if (!IsReachable(from)) return path;
            var cur = from;
            path.Add(cur);
            int guard = _grid.Width * _grid.Height + 1;
            while (guard-- > 0 && Distance(cur) > 0)
            {
                if (!TryGetNextStep(cur, out cur)) break;
                path.Add(cur);
            }
            return path;
        }
    }

    /// <summary>Caches one PathField per movement class and recomputes all on tide turns.</summary>
    public sealed class PathService
    {
        private readonly TileGrid _grid;
        private readonly PathField[] _fields;

        public PathService(TileGrid grid)
        {
            _grid = grid;
            _fields = new PathField[3];
            _fields[(int)MoveClass.Terrestrial] = new PathField(grid, MoveClass.Terrestrial);
            _fields[(int)MoveClass.Amphibious] = new PathField(grid, MoveClass.Amphibious);
            _fields[(int)MoveClass.Pelagic] = new PathField(grid, MoveClass.Pelagic);
        }

        public PathField For(MoveClass c) => _fields[(int)c];

        /// <summary>Recompute all fields (call on tide turn or when a tower is built/sold —
        /// towers occupy BuildPlots which are never walkable, so only tide turns matter).</summary>
        public void RecomputeAll()
        {
            foreach (var f in _fields) f.Recompute();
        }
    }
}
