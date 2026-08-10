using System;

namespace Tidewatch.Core
{
    /// <summary>Integer grid coordinate. Pure value type, no engine dependency.</summary>
    public readonly struct GridPos : IEquatable<GridPos>
    {
        public readonly int X;
        public readonly int Y;

        public GridPos(int x, int y)
        {
            X = x;
            Y = y;
        }

        public bool Equals(GridPos other) => X == other.X && Y == other.Y;
        public override bool Equals(object obj) => obj is GridPos p && Equals(p);
        public override int GetHashCode() => (X * 397) ^ Y;
        public override string ToString() => $"({X},{Y})";

        public static bool operator ==(GridPos a, GridPos b) => a.Equals(b);
        public static bool operator !=(GridPos a, GridPos b) => !a.Equals(b);

        public static GridPos operator +(GridPos a, GridPos b) => new GridPos(a.X + b.X, a.Y + b.Y);

        /// <summary>Manhattan distance.</summary>
        public static int Manhattan(GridPos a, GridPos b) =>
            Math.Abs(a.X - b.X) + Math.Abs(a.Y - b.Y);

        /// <summary>Squared Euclidean distance, as float for range checks.</summary>
        public static float SqrDistance(GridPos a, GridPos b)
        {
            float dx = a.X - b.X;
            float dy = a.Y - b.Y;
            return dx * dx + dy * dy;
        }
    }
}
