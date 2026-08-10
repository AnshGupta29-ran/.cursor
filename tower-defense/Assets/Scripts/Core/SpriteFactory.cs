using System.Collections.Generic;
using UnityEngine;

namespace TD.Core
{
    /// <summary>Procedurally generated sprites so the game has a coherent look with zero art assets.</summary>
    public static class SpriteFactory
    {
        static readonly Dictionary<string, Sprite> _cache = new Dictionary<string, Sprite>();

        public static Sprite Circle(float softness = 0.12f, int size = 64) =>
            Get($"circle_{size}_{softness}", size, (x, y, r) =>
                Mathf.Clamp01((1f - r) / Mathf.Max(softness, 0.001f)));

        public static Sprite Ring(float thickness = 0.1f, int size = 128) =>
            Get($"ring_{size}_{thickness}", size, (x, y, r) =>
            {
                float d = Mathf.Abs(r - (1f - thickness));
                return Mathf.Clamp01(1f - d / thickness);
            });

        public static Sprite Square(int size = 32) =>
            Get($"square_{size}", size, (x, y, r) => 1f);

        public static Sprite RoundedSquare(float radius = 0.25f, int size = 64) =>
            Get($"rsquare_{size}_{radius}", size, (x, y, r) =>
            {
                float ax = Mathf.Abs(x), ay = Mathf.Abs(y);
                float q = Mathf.Max(ax, ay);
                if (q < 1f - radius) return 1f;
                float cx = Mathf.Max(ax - (1f - radius), 0f);
                float cy = Mathf.Max(ay - (1f - radius), 0f);
                return Mathf.Clamp01(1f - (Mathf.Sqrt(cx * cx + cy * cy) / radius - 1f) * 2f);
            });

        public static Sprite Diamond(int size = 64) =>
            Get($"diamond_{size}", size, (x, y, r) =>
            {
                float m = (Mathf.Abs(x) + Mathf.Abs(y)) / 1.4f;
                return Mathf.Clamp01((1f - m) * 8f);
            });

        public static Sprite Triangle(int size = 64) =>
            Get($"triangle_{size}", size, (x, y, r) =>
            {
                // y in [-1,1]; triangle pointing up
                float half = Mathf.Lerp(1f, 0f, (y + 1f) / 2f);
                return Mathf.Abs(x) < half ? 1f : 0f;
            });

        public static Sprite Star(int size = 64) =>
            Get($"star_{size}", size, (x, y, r) =>
            {
                float angle = Mathf.Atan2(y, x);
                float wobble = 0.75f + 0.25f * Mathf.Cos(angle * 5f);
                return Mathf.Clamp01((wobble - r) * 10f);
            });

        delegate float ShapeFunc(float x, float y, float r);

        static Sprite Get(string key, int size, ShapeFunc f)
        {
            if (_cache.TryGetValue(key, out var s)) return s;
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false)
            {
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp,
            };
            var px = new Color[size * size];
            float half = size / 2f;
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float nx = (x + 0.5f - half) / half;
                    float ny = (y + 0.5f - half) / half;
                    float a = Mathf.Clamp01(f(nx, ny, Mathf.Sqrt(nx * nx + ny * ny)));
                    px[y * size + x] = new Color(1f, 1f, 1f, a);
                }
            }
            tex.SetPixels(px);
            tex.Apply();
            s = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), size / 2f);
            s.name = key;
            _cache[key] = s;
            return s;
        }
    }
}
