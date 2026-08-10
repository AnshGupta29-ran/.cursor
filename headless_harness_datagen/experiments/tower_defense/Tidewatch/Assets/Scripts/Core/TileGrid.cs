using System;
using System.Collections.Generic;

namespace Tidewatch.Core
{
    /// <summary>One tile: base terrain + whether it's currently underwater.</summary>
    public sealed class Tile
    {
        public TerrainType Terrain;
        /// <summary>True when flooded by tide, or permanently for DeepWater.</summary>
        public bool IsWater;
        /// <summary>Tower id occupying a BuildPlot; null if empty.</summary>
        public string OccupiedByTowerId;

        /// <summary>Can enemies of any class ever be on this tile (ignores tide)?</summary>
        public bool IsEverTraversable =>
            Terrain == TerrainType.Causeway || Terrain == TerrainType.Trench ||
            Terrain == TerrainType.DeepWater || Terrain == TerrainType.Gate ||
            Terrain == TerrainType.Base;
    }

    /// <summary>
    /// The level grid. Knows terrain, current flood state from the tide, and answers
    /// pathability per movement class. Pure C#, unit-testable.
    /// </summary>
    public sealed class TileGrid
    {
        public int Width { get; }
        public int Height { get; }
        private readonly Tile[,] _tiles;
        public GridPos BasePos { get; private set; }
        private readonly List<GridPos> _gates = new List<GridPos>();
        public IReadOnlyList<GridPos> Gates => _gates;

        public TileGrid(int width, int height)
        {
            Width = width;
            Height = height;
            _tiles = new Tile[width, height];
            for (int x = 0; x < width; x++)
                for (int y = 0; y < height; y++)
                    _tiles[x, y] = new Tile { Terrain = TerrainType.Rock };
        }

        public bool InBounds(GridPos p) => p.X >= 0 && p.Y >= 0 && p.X < Width && p.Y < Height;
        public Tile Get(GridPos p) => InBounds(p) ? _tiles[p.X, p.Y] : null;

        public void SetTerrain(GridPos p, TerrainType t)
        {
            _tiles[p.X, p.Y].Terrain = t;
            if (t == TerrainType.Base) BasePos = p;
            if (t == TerrainType.Gate && !_gates.Contains(p)) _gates.Add(p);
        }

        /// <summary>Set whether a tile is currently flooded. DeepWater is always water.</summary>
        public void SetFlooded(GridPos p, bool flooded)
        {
            var tile = _tiles[p.X, p.Y];
            if (tile.Terrain == TerrainType.DeepWater) { tile.IsWater = true; return; }
            if (tile.Terrain == TerrainType.Causeway || tile.Terrain == TerrainType.Trench)
                tile.IsWater = flooded;
        }

        /// <summary>Apply a full tide phase: floods/drains all tiles per phase rules.</summary>
        public void ApplyTidePhase(TidePhase phase)
        {
            bool highWater = phase == TidePhase.High || phase == TidePhase.Rising;
            bool lowWater = phase == TidePhase.Low || phase == TidePhase.Ebbing;
            for (int x = 0; x < Width; x++)
            {
                for (int y = 0; y < Height; y++)
                {
                    var t = _tiles[x, y];
                    switch (t.Terrain)
                    {
                        case TerrainType.Causeway:
                            // Causeways flood only at High tide.
                            t.IsWater = phase == TidePhase.High;
                            break;
                        case TerrainType.Trench:
                            // Trenches are flooded except at Low tide (they drain).
                            t.IsWater = phase != TidePhase.Low;
                            break;
                        case TerrainType.DeepWater:
                            t.IsWater = true;
                            break;
                        default:
                            t.IsWater = false;
                            break;
                    }
                }
            }
        }

        /// <summary>
        /// Whether an enemy of the given movement class can occupy this tile right now.
        /// BuildPlots, Rock are never walkable. Gates/Base are walkable for pathing.
        /// </summary>
        public bool IsWalkable(GridPos p, MoveClass moveClass)
        {
            var t = Get(p);
            if (t == null) return false;
            switch (t.Terrain)
            {
                case TerrainType.Rock:
                case TerrainType.BuildPlot:
                    return false;
                case TerrainType.Gate:
                case TerrainType.Base:
                    return true; // entry/exit always allowed
                case TerrainType.DeepWater:
                    return moveClass == MoveClass.Pelagic;
                case TerrainType.Causeway:
                case TerrainType.Trench:
                    if (t.IsWater)
                        return moveClass != MoveClass.Terrestrial; // amphibious + pelagic
                    else
                        return moveClass != MoveClass.Pelagic;     // terrestrial + amphibious
                default:
                    return false;
            }
        }

        /// <summary>Can a tower be built here?</summary>
        public bool IsBuildable(GridPos p)
        {
            var t = Get(p);
            return t != null && t.Terrain == TerrainType.BuildPlot && t.OccupiedByTowerId == null;
        }

        public bool TryPlaceTower(GridPos p, string towerId)
        {
            if (!IsBuildable(p)) return false;
            _tiles[p.X, p.Y].OccupiedByTowerId = towerId;
            return true;
        }

        public bool TryRemoveTower(GridPos p)
        {
            var t = Get(p);
            if (t == null || t.Terrain != TerrainType.BuildPlot || t.OccupiedByTowerId == null) return false;
            t.OccupiedByTowerId = null;
            return true;
        }

        /// <summary>4-connected neighbours.</summary>
        public IEnumerable<GridPos> Neighbours(GridPos p)
        {
            if (InBounds(new GridPos(p.X + 1, p.Y))) yield return new GridPos(p.X + 1, p.Y);
            if (InBounds(new GridPos(p.X - 1, p.Y))) yield return new GridPos(p.X - 1, p.Y);
            if (InBounds(new GridPos(p.X, p.Y + 1))) yield return new GridPos(p.X, p.Y + 1);
            if (InBounds(new GridPos(p.X, p.Y - 1))) yield return new GridPos(p.X, p.Y - 1);
        }
    }
}
