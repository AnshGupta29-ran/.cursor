using System.Collections.Generic;
using UnityEngine;

namespace TD.Core
{
    /// <summary>Lightweight pooled visual effects: bursts, rings, tracers, floating text.</summary>
    public class Effects : MonoBehaviour
    {
        public static Effects Instance { get; private set; }

        const int PoolSize = 96;
        readonly List<Puff> _puffs = new List<Puff>();
        readonly List<Tracer> _tracers = new List<Tracer>();
        readonly List<FloatText> _texts = new List<FloatText>();

        class Puff
        {
            public SpriteRenderer renderer;
            public float t, duration, startScale, endScale;
            public Color color;
            public Vector3 velocity;
            public bool active;
        }
        class Tracer
        {
            public LineRenderer line;
            public float t, duration;
            public bool active;
        }
        class FloatText
        {
            public TextMesh mesh;
            public float t, duration;
            public Vector3 velocity;
            public bool active;
        }

        void Awake()
        {
            Instance = this;
            var puffSprite = SpriteFactory.Circle();
            for (int i = 0; i < PoolSize; i++)
            {
                var go = new GameObject("puff");
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = puffSprite;
                sr.sortingOrder = 50;
                go.SetActive(false);
                _puffs.Add(new Puff { renderer = sr });
            }
            for (int i = 0; i < 24; i++)
            {
                var go = new GameObject("tracer");
                go.transform.SetParent(transform, false);
                var lr = go.AddComponent<LineRenderer>();
                lr.material = MaterialLibrary.Line;
                lr.positionCount = 2;
                lr.startWidth = 0.06f; lr.endWidth = 0.02f;
                lr.sortingOrder = 45;
                go.SetActive(false);
                _tracers.Add(new Tracer { line = lr });
            }
            for (int i = 0; i < 32; i++)
            {
                var go = new GameObject("floatText");
                go.transform.SetParent(transform, false);
                var tm = go.AddComponent<TextMesh>();
                tm.anchor = TextAnchor.MiddleCenter;
                tm.alignment = TextAlignment.Center;
                tm.characterSize = 0.18f;
                tm.fontSize = 60;
                tm.color = Color.white;
                go.SetActive(false);
                _texts.Add(new FloatText { mesh = tm });
            }
        }

        public static void Burst(Vector3 pos, Color color, int count = 8, float speed = 2.5f, float size = 0.16f, float duration = 0.5f)
        {
            if (Instance == null) return;
            for (int i = 0; i < count; i++)
            {
                var p = Instance._puffs.Find(x => !x.active);
                if (p == null) return;
                p.active = true; p.t = 0f; p.duration = duration;
                p.color = color;
                p.startScale = size; p.endScale = size * 0.3f;
                float a = Random.Range(0f, Mathf.PI * 2f);
                float v = Random.Range(speed * 0.4f, speed);
                p.velocity = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * v;
                var tr = p.renderer.transform;
                tr.position = pos + new Vector3(0, 0, -0.5f);
                tr.localScale = Vector3.one * size;
                p.renderer.color = color;
                p.renderer.gameObject.SetActive(true);
            }
        }

        public static void RingFlash(Vector3 pos, Color color, float scale = 0.6f, float duration = 0.3f)
        {
            Burst(pos, color, 1, 0f, scale, duration);
        }

        public static void FireTracer(Vector3 from, Vector3 to, Color color, float duration = 0.09f)
        {
            if (Instance == null) return;
            var t = Instance._tracers.Find(x => !x.active);
            if (t == null) return;
            t.active = true; t.t = 0f; t.duration = duration;
            t.line.SetPosition(0, from + new Vector3(0, 0, -0.6f));
            t.line.SetPosition(1, to + new Vector3(0, 0, -0.6f));
            t.line.startColor = color; t.line.endColor = color;
            t.line.gameObject.SetActive(true);
        }

        public static void SpawnText(Vector3 pos, string text, Color color, float duration = 0.9f)
        {
            if (Instance == null) return;
            var f = Instance._texts.Find(x => !x.active);
            if (f == null) return;
            f.active = true; f.t = 0f; f.duration = duration;
            f.velocity = new Vector3(0f, 1.2f, 0f);
            f.mesh.text = text;
            f.mesh.color = color;
            f.mesh.transform.position = pos + new Vector3(0, 0.4f, -0.7f);
            f.mesh.gameObject.SetActive(true);
        }

        void Update()
        {
            float dt = Time.deltaTime;
            foreach (var p in _puffs)
            {
                if (!p.active) continue;
                p.t += dt;
                float k = p.t / p.duration;
                if (k >= 1f) { p.active = false; p.renderer.gameObject.SetActive(false); continue; }
                var tr = p.renderer.transform;
                tr.position += p.velocity * dt;
                tr.localScale = Vector3.one * Mathf.Lerp(p.startScale, p.endScale, k);
                var c = p.color; c.a = 1f - k;
                p.renderer.color = c;
            }
            foreach (var t in _tracers)
            {
                if (!t.active) continue;
                t.t += dt;
                float k = t.t / t.duration;
                if (k >= 1f) { t.active = false; t.line.gameObject.SetActive(false); continue; }
                var c = t.line.startColor; c.a = 1f - k;
                t.line.startColor = c; t.line.endColor = c;
            }
            foreach (var f in _texts)
            {
                if (!f.active) continue;
                f.t += dt;
                float k = f.t / f.duration;
                if (k >= 1f) { f.active = false; f.mesh.gameObject.SetActive(false); continue; }
                f.mesh.transform.position += f.velocity * dt;
                var c = f.mesh.color; c.a = 1f - k * k;
                f.mesh.color = c;
            }
        }
    }

    /// <summary>Shared materials (built-in pipeline).</summary>
    public static class MaterialLibrary
    {
        static Material _line;
        public static Material Line
        {
            get
            {
                if (_line == null)
                {
                    _line = new Material(Shader.Find("Sprites/Default"));
                }
                return _line;
            }
        }
    }
}
