using System.Collections.Generic;
using TD.Enemies;
using UnityEngine;

namespace TD.Towers
{
    /// <summary>Pooled projectile: homing (arrows, frost) or arcing (cannon shells).</summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class Projectile : MonoBehaviour
    {
        static readonly List<Projectile> _pool = new List<Projectile>();

        public enum FlightMode { Homing, Arc }

        FlightMode _mode;
        Enemy _target;
        Vector3 _targetPos;
        float _speed, _damage, _splash, _slowAmount, _slowDuration, _armorPierce;
        Color _color;
        Vector3 _arcStart;
        float _arcT, _arcDuration;
        SpriteRenderer _sr;
        TrailRenderer _trail;
        bool _active;

        public static Projectile Fire(
            Vector3 from, Enemy target, float speed, float damage,
            float splash, float slowAmount, float slowDuration, float armorPierce,
            Color color, bool arc)
        {
            var p = Get();
            p._mode = arc ? FlightMode.Arc : FlightMode.Homing;
            p._target = target;
            p._targetPos = target != null ? target.transform.position : from + Vector3.right;
            p._speed = speed; p._damage = damage; p._splash = splash;
            p._slowAmount = slowAmount; p._slowDuration = slowDuration;
            p._armorPierce = armorPierce;
            p._color = color;
            p.transform.position = from;
            p._sr.color = color;
            p._sr.sprite = arc ? Core.SpriteFactory.Circle() : Core.SpriteFactory.Diamond();
            p.transform.localScale = Vector3.one * (arc ? 0.22f : 0.16f);
            if (arc)
            {
                p._arcStart = from;
                p._arcT = 0f;
                p._arcDuration = Mathf.Max(0.25f, Vector3.Distance(from, p._targetPos) / speed);
            }
            p._active = true;
            p.gameObject.SetActive(true);
            return p;
        }

        static Projectile Get()
        {
            foreach (var p in _pool)
                if (!p._active) return p;
            var go = new GameObject("projectile");
            var p = go.AddComponent<Projectile>();
            _pool.Add(p);
            return p;
        }

        void Awake()
        {
            _sr = GetComponent<SpriteRenderer>();
            _sr.sortingOrder = 30;
            var trailGo = new GameObject("trail");
            trailGo.transform.SetParent(transform, false);
            _trail = trailGo.AddComponent<TrailRenderer>();
            _trail.material = Core.MaterialLibrary.Line;
            _trail.startWidth = 0.05f; _trail.endWidth = 0f;
            _trail.time = 0.15f;
            _trail.startColor = new Color(1f, 1f, 1f, 0.5f);
            _trail.endColor = new Color(1f, 1f, 1f, 0f);
            _trail.sortingOrder = 29;
            gameObject.SetActive(false);
        }

        void Update()
        {
            if (!_active) return;
            float dt = Time.deltaTime;

            if (_mode == FlightMode.Homing)
            {
                if (_target != null) _targetPos = _target.transform.position;
                var to = _targetPos - transform.position;
                float step = _speed * dt;
                if (to.magnitude <= step)
                {
                    Impact(_targetPos);
                    return;
                }
                transform.position += to.normalized * step;
                float a = Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg;
                transform.rotation = Quaternion.Euler(0, 0, a);
            }
            else // Arc
            {
                if (_target != null) _targetPos = _target.transform.position;
                _arcT += dt / _arcDuration;
                if (_arcT >= 1f)
                {
                    Impact(_targetPos);
                    return;
                }
                var pos = Vector3.Lerp(_arcStart, _targetPos, _arcT);
                pos.y += Mathf.Sin(_arcT * Mathf.PI) * 0.8f; // parabola
                transform.position = pos;
            }
        }

        void Impact(Vector3 at)
        {
            if (_splash > 0.05f)
            {
                Core.Effects.Burst(at, _color, 12, 3.2f, 0.15f);
                Core.Effects.RingFlash(at, _color, _splash * 0.9f, 0.25f);
                AudioManager.Instance?.Play(SfxId.CannonHit);
                var hits = new List<Enemy>(Enemy.All);
                foreach (var e in hits)
                {
                    if (e == null || e.IsDead) continue;
                    float d = Vector3.Distance(at, e.transform.position);
                    if (d <= _splash)
                    {
                        float falloff = 1f - 0.5f * (d / _splash);
                        e.TakeDamage(_damage * falloff, _armorPierce);
                        if (_slowAmount > 0f) e.ApplySlow(_slowAmount, _slowDuration);
                    }
                }
            }
            else
            {
                Core.Effects.Burst(at, _color, 5, 2f, 0.1f);
                if (_target != null && !_target.IsDead)
                {
                    _target.TakeDamage(_damage, _armorPierce);
                    if (_slowAmount > 0f)
                    {
                        _target.ApplySlow(_slowAmount, _slowDuration);
                        Core.Effects.RingFlash(at, new Color(0.5f, 0.85f, 1f), 0.4f, 0.2f);
                        AudioManager.Instance?.Play(SfxId.FrostHit);
                    }
                }
            }
            Despawn();
        }

        void Despawn()
        {
            _active = false;
            _target = null;
            if (_trail != null) _trail.Clear();
            gameObject.SetActive(false);
        }

        public static void ClearAll()
        {
            foreach (var p in _pool)
                if (p._active) p.Despawn();
        }
    }
}
